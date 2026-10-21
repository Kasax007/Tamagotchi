package net.kasax.tamagotchi.pet;

import java.util.EnumSet;
import java.util.List;
import java.util.function.Predicate;
import net.kasax.tamagotchi.block.BouncyMushroomBlock;
import net.kasax.tamagotchi.block.FoodBowlBlock;
import net.kasax.tamagotchi.block.PetBathBlock;
import net.kasax.tamagotchi.block.PetBedBlock;
import net.kasax.tamagotchi.block.PetHouseBlock;
import net.kasax.tamagotchi.block.RunningWheelBlock;
import net.kasax.tamagotchi.block.ScratchingPostBlock;
import net.kasax.tamagotchi.item.LaserPointerItem;
import net.kasax.tamagotchi.pet.PetNeeds.Mood;
import net.kasax.tamagotchi.pet.PetNeeds.Need;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.entity.ai.goal.GoalSelector;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.PanicGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.SitWhenOrderedToGoal;
import net.minecraft.world.entity.ai.goal.TemptGoal;
import net.minecraft.world.entity.ai.goal.WaterAvoidingRandomStrollGoal;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.OwnerHurtTargetGoal;
import net.minecraft.world.entity.ai.util.DefaultRandomPos;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.FireworkRocketEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CakeBlock;
import net.minecraft.world.level.block.CampfireBlock;
import net.minecraft.world.level.block.entity.JukeboxBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** All pet AI goals, registered in one place. */
public final class PetGoals {
    private PetGoals() {
    }

    public static void register(TamaPet pet, GoalSelector goals, GoalSelector targets) {
        PetSpecies s = pet.species();
        if (s.gait() != PetSpecies.Gait.SWIM && s != PetSpecies.MIMIC) {
            goals.addGoal(0, new FloatGoal(pet));
        }
        goals.addGoal(1, new WildPanicGoal(pet));
        goals.addGoal(1, new SleepGoal(pet));
        goals.addGoal(2, new SitWhenOrderedToGoal(pet));
        goals.addGoal(2, new RetreatGoal(pet));
        goals.addGoal(3, new FeedOwnerGoal(pet));
        goals.addGoal(3, new WildTemptGoal(pet));
        goals.addGoal(4, new PetAttackGoal(pet));
        goals.addGoal(5, new ChaseLaserGoal(pet));
        goals.addGoal(5, new FetchGoal(pet));
        goals.addGoal(6, new PetFollowGoal(pet));
        goals.addGoal(7, new UseBlockGoal(pet));
        goals.addGoal(8, new ReactGoal(pet));
        goals.addGoal(9, new PetStrollGoal(pet));
        goals.addGoal(10, new LookAtPlayerGoal(pet, Player.class, 8.0F));
        goals.addGoal(10, new RandomLookAroundGoal(pet));

        targets.addGoal(1, new OwnerHurtByTargetGoal(pet));
        targets.addGoal(2, new OwnerHurtTargetGoal(pet));
        targets.addGoal(3, new PetHurtByTargetGoal(pet));
    }

    static boolean busy(TamaPet pet) {
        return pet.isSleeping() || pet.isOrderedToSit() || pet.getTarget() != null || pet.isLeashed();
    }

    static boolean dangerous(PetSpecies s) {
        return s == PetSpecies.EMBER_PUP || s == PetSpecies.SCULK_WISP || s == PetSpecies.MIMIC;
    }

    // =====================================================================================
    // wild behaviour

    static final class WildPanicGoal extends PanicGoal {
        private final TamaPet pet;

        WildPanicGoal(TamaPet pet) {
            super(pet, 1.5);
            this.pet = pet;
        }

        @Override
        public boolean canUse() {
            return !this.pet.isTame() && !dangerous(this.pet.species()) && super.canUse();
        }
    }

    static final class WildTemptGoal extends TemptGoal {
        private final TamaPet pet;

        WildTemptGoal(TamaPet pet) {
            super(pet, 1.0, s -> s.is(ModItems.TAMAGOTCHI_HEART), false);
            this.pet = pet;
        }

        @Override
        public boolean canUse() {
            return !this.pet.isTame() && super.canUse();
        }
    }

    static final class PetHurtByTargetGoal extends HurtByTargetGoal {
        private final TamaPet pet;

        PetHurtByTargetGoal(TamaPet pet) {
            super(pet);
            this.pet = pet;
        }

        @Override
        public boolean canUse() {
            return (this.pet.isTame() || dangerous(this.pet.species())) && super.canUse();
        }
    }

    // =====================================================================================
    // following / wandering

    /** Like vanilla FollowOwnerGoal, but works with every navigation (the Tide Dragon swims). */
    static final class PetFollowGoal extends Goal {
        private final TamaPet pet;
        private @Nullable LivingEntity owner;
        private int recalc;

        PetFollowGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            LivingEntity o = this.pet.getOwner();
            if (o == null || this.pet.mode() != TamaPet.Mode.FOLLOW || this.pet.isSleeping() || this.pet.unableToMoveToOwner()) {
                return false;
            }
            if (this.pet.distanceToSqr(o) < 9.0 * 9.0) {
                return false;
            }
            this.owner = o;
            return true;
        }

        @Override
        public boolean canContinueToUse() {
            return this.owner != null && !this.pet.getNavigation().isDone() && !this.pet.unableToMoveToOwner()
                    && this.pet.mode() == TamaPet.Mode.FOLLOW && !this.pet.isSleeping() && this.pet.distanceToSqr(this.owner) > 2.5 * 2.5;
        }

        @Override
        public void start() {
            this.recalc = 0;
        }

        @Override
        public void stop() {
            this.owner = null;
            this.pet.getNavigation().stop();
        }

        @Override
        public void tick() {
            if (this.owner == null) {
                return;
            }
            this.pet.getLookControl().setLookAt(this.owner, 10.0F, this.pet.getMaxHeadXRot());
            if (this.pet.shouldTryTeleportToOwner()) {
                this.pet.tryToTeleportToOwner();
            } else if (--this.recalc <= 0) {
                this.recalc = 10;
                this.pet.getNavigation().moveTo(this.owner, 1.15);
            }
        }
    }

    /** Strolls around its home: the structure for wild pets, the wander spot in wander mode. */
    static final class PetStrollGoal extends WaterAvoidingRandomStrollGoal {
        private final TamaPet pet;

        PetStrollGoal(TamaPet pet) {
            super(pet, 0.8);
            this.pet = pet;
        }

        @Override
        public boolean canUse() {
            return !this.pet.isSleeping() && !this.pet.isOrderedToSit() && super.canUse();
        }

        @Override
        protected @Nullable Vec3 getPosition() {
            BlockPos home = this.pet.home();
            boolean anchored = !this.pet.isTame() || this.pet.mode() == TamaPet.Mode.WANDER;
            if (anchored && home != null && !home.closerToCenterThan(this.pet.position(), 9.0)) {
                return DefaultRandomPos.getPosTowards(this.pet, 8, 4, Vec3.atBottomCenterOf(home), Math.PI / 2);
            }
            return super.getPosition();
        }
    }

    // =====================================================================================
    // sleep

    static final class SleepGoal extends Goal {
        private final TamaPet pet;
        private @Nullable BlockPos bed;
        private int searchTicks;

        SleepGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        private boolean sleepy() {
            if (!this.pet.isTame() || this.pet.getTarget() != null || this.pet.isInWater() || this.pet.isLeashed()) {
                return false;
            }
            PetNeeds n = this.pet.needs();
            LivingEntity owner = this.pet.getOwner();
            boolean night = this.pet.level().isDarkOutside();
            if (owner != null && owner.isSleeping() && this.pet.distanceToSqr(owner) < 400) {
                return true;
            }
            if (n.energy < 18) {
                return true;
            }
            return night && n.energy < 90 && this.pet.mode() != TamaPet.Mode.FOLLOW;
        }

        @Override
        public boolean canUse() {
            return this.pet.isSleeping() || sleepy();
        }

        @Override
        public void start() {
            this.bed = findBed();
            this.searchTicks = 0;
            if (this.bed != null) {
                this.pet.getNavigation().moveTo(this.bed.getX() + 0.5, this.bed.getY(), this.bed.getZ() + 0.5, 1.0);
            }
        }

        private @Nullable BlockPos findBed() {
            LivingEntity owner = this.pet.getOwner();
            if (owner != null && owner.isSleeping()) {
                return owner.getSleepingPos().map(p -> {
                    for (Direction d : Direction.Plane.HORIZONTAL) {
                        BlockPos n = p.relative(d, 2);
                        if (this.pet.level().getBlockState(n).isAir()) {
                            return n;
                        }
                    }
                    return null;
                }).orElse(null);
            }
            return BlockSearch.nearest(this.pet, 10, 3, st -> st.getBlock() instanceof PetBedBlock);
        }

        @Override
        public void tick() {
            if (this.pet.isSleeping()) {
                return;
            }
            this.searchTicks++;
            boolean arrived = this.bed == null || this.pet.blockPosition().closerThan(this.bed, 1.5)
                    || this.searchTicks > 120 || this.pet.getNavigation().isDone();
            if (arrived) {
                if (this.bed != null && this.pet.blockPosition().closerThan(this.bed, 2.5)
                        && this.pet.level().getBlockState(this.bed).getBlock() instanceof PetBedBlock) {
                    this.pet.snapTo(this.bed.getX() + 0.5, this.bed.getY() + 0.2, this.bed.getZ() + 0.5, this.pet.getYRot(), 0);
                }
                this.pet.setSleeping(true);
                this.pet.playSound(ModSounds.PET_YAWN, 0.5F, this.pet.getVoicePitch());
            }
        }

        @Override
        public boolean canContinueToUse() {
            if (!this.pet.isTame() || this.pet.getTarget() != null || this.pet.hurtTime > 0) {
                return false;
            }
            PetNeeds n = this.pet.needs();
            LivingEntity owner = this.pet.getOwner();
            boolean night = this.pet.level().isDarkOutside();
            if (owner != null && this.pet.mode() == TamaPet.Mode.FOLLOW && !owner.isSleeping()
                    && (this.pet.distanceToSqr(owner) > 100 || n.energy > 40)) {
                return false;
            }
            return n.energy < 100 || night && this.pet.mode() != TamaPet.Mode.FOLLOW;
        }

        @Override
        public void stop() {
            this.pet.wakeUp();
            this.bed = null;
        }
    }

    // =====================================================================================
    // low health: run to the owner and eat food from the backpack

    static final class RetreatGoal extends Goal {
        private final TamaPet pet;
        private int eatCooldown;

        RetreatGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            return this.pet.isTame() && !this.pet.isOrderedToSit() && this.pet.getOwner() != null
                    && this.pet.getHealth() < this.pet.getMaxHealth() * 0.35F;
        }

        @Override
        public boolean canContinueToUse() {
            return this.pet.isTame() && this.pet.getOwner() != null && this.pet.getHealth() < this.pet.getMaxHealth() * 0.6F;
        }

        @Override
        public void start() {
            this.pet.setTarget(null);
            this.pet.setFlag(TamaPet.F_SCARED, true);
            this.eatCooldown = 10;
        }

        @Override
        public void tick() {
            LivingEntity owner = this.pet.getOwner();
            if (owner == null) {
                return;
            }
            this.pet.setTarget(null);
            if (this.pet.distanceToSqr(owner) > 6) {
                Vec3 behind = owner.position().subtract(owner.getLookAngle().scale(1.5));
                this.pet.getNavigation().moveTo(behind.x, behind.y, behind.z, 1.35);
            } else {
                this.pet.getNavigation().stop();
                this.pet.getLookControl().setLookAt(owner);
            }
            if (--this.eatCooldown <= 0) {
                this.eatCooldown = 50;
                int slots = this.pet.storageSlots();
                for (int i = 0; i < slots; i++) {
                    ItemStack st = this.pet.inventory().getItem(i);
                    if (!st.isEmpty() && (st.has(DataComponents.FOOD) || this.pet.isPetFood(st))) {
                        ItemStack one = st.split(1);
                        this.pet.inventory().setChanged();
                        this.pet.eat(one);
                        this.pet.heal(4.0F + this.pet.foodValue(one) / 6.0F);
                        break;
                    }
                }
            }
        }

        @Override
        public void stop() {
            this.pet.setFlag(TamaPet.F_SCARED, false);
        }
    }

    // =====================================================================================
    // golden apples for the owner

    static final class FeedOwnerGoal extends Goal {
        private final TamaPet pet;
        private int cooldown;
        private int timer;
        private boolean fed;

        FeedOwnerGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private boolean ownerNeedsHelp() {
            LivingEntity owner = this.pet.getOwner();
            return owner != null && owner.isAlive() && owner.level() == this.pet.level()
                    && owner.getHealth() <= Math.max(6.0F, owner.getMaxHealth() * 0.3F)
                    && this.pet.distanceToSqr(owner) < 24 * 24;
        }

        @Override
        public boolean canUse() {
            if (this.cooldown > 0) {
                this.cooldown--;
                return false;
            }
            return this.pet.isTame() && this.pet.snacks() > 0 && !this.pet.isOrderedToSit() && ownerNeedsHelp();
        }

        @Override
        public boolean canContinueToUse() {
            return !this.fed && this.timer < 200 && this.pet.snacks() > 0 && ownerNeedsHelp();
        }

        @Override
        public void start() {
            this.timer = 0;
            this.fed = false;
            this.pet.wakeUp();
            this.pet.setTarget(null);
        }

        @Override
        public void tick() {
            LivingEntity owner = this.pet.getOwner();
            if (owner == null) {
                return;
            }
            this.timer++;
            this.pet.getLookControl().setLookAt(owner);
            if (this.pet.distanceToSqr(owner) > 4.5) {
                this.pet.getNavigation().moveTo(owner, 1.5);
                return;
            }
            this.pet.getNavigation().stop();
            if (this.pet.currentAction() != PetAction.FEED_OWNER) {
                this.pet.playAction(PetAction.FEED_OWNER);
                return;
            }
            if (!this.fed && this.pet.level() instanceof ServerLevel level) {
                ItemStack apple = new ItemStack(Items.GOLDEN_APPLE);
                apple.finishUsingItem(level, owner);
                this.pet.setSnacks(this.pet.snacks() - 1);
                this.pet.playSound(ModSounds.PET_FEED_OWNER, 1.0F, 1.0F);
                level.sendParticles(ModParticles.HEART, owner.getX(), owner.getY() + 1.7, owner.getZ(), 5, 0.3, 0.2, 0.3, 0.0);
                if (owner instanceof Player p) {
                    p.sendOverlayMessage(Component.translatable("message.tamagotchi.fed_you", this.pet.getName(), this.pet.snacks()));
                }
                this.pet.needs().addBond(1.5F);
                this.fed = true;
                this.cooldown = 20 * 25;
            }
        }
    }

    // =====================================================================================
    // combat

    static final class PetAttackGoal extends Goal {
        private final TamaPet pet;
        private int cooldown;
        private int repath;

        PetAttackGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        private boolean willing() {
            if (this.pet.isOrderedToSit()) {
                return false;
            }
            if (!this.pet.isTame()) {
                return true;
            }
            return this.pet.needs().mood() != Mood.MISERABLE && this.pet.getHealth() >= this.pet.getMaxHealth() * 0.35F;
        }

        @Override
        public boolean canUse() {
            LivingEntity t = this.pet.getTarget();
            return t != null && t.isAlive() && willing();
        }

        @Override
        public boolean canContinueToUse() {
            return canUse() && this.pet.distanceToSqr(this.pet.getTarget()) < 32 * 32;
        }

        @Override
        public void start() {
            this.pet.wakeUp();
            this.repath = 0;
        }

        @Override
        public void stop() {
            this.pet.getNavigation().stop();
        }

        @Override
        public void tick() {
            LivingEntity target = this.pet.getTarget();
            if (target == null) {
                return;
            }
            this.pet.getLookControl().setLookAt(target, 30.0F, 30.0F);
            double range = this.pet.species().attackStyle().range;
            double reach = range + this.pet.getBbWidth() * 0.5 + target.getBbWidth() * 0.5;
            double dist = this.pet.distanceTo(target);
            boolean see = this.pet.getSensing().hasLineOfSight(target);
            if (dist > reach * 0.85 || !see) {
                if (--this.repath <= 0) {
                    this.repath = 8;
                    this.pet.getNavigation().moveTo(target, 1.25);
                }
            } else if (this.pet.species().attackStyle().ranged) {
                this.pet.getNavigation().stop();
            }
            if (this.cooldown > 0) {
                this.cooldown--;
            } else if (dist <= reach && see && this.pet.level() instanceof ServerLevel level) {
                this.cooldown = Talents.attack(this.pet, level, target);
            }
        }
    }

    // =====================================================================================
    // toys

    static final class ChaseLaserGoal extends Goal {
        private final TamaPet pet;
        private int pounceCooldown;
        private int pounces;

        ChaseLaserGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        private @Nullable Vec3 dot() {
            if (!this.pet.isTame() || this.pet.ownerUuid() == null) {
                return null;
            }
            Vec3 dot = LaserPointerItem.activeDot(this.pet.level(), this.pet.ownerUuid());
            return dot != null && dot.distanceToSqr(this.pet.position()) < 24 * 24 ? dot : null;
        }

        @Override
        public boolean canUse() {
            return !busy(this.pet) && dot() != null;
        }

        @Override
        public boolean canContinueToUse() {
            return !this.pet.isOrderedToSit() && this.pet.getTarget() == null && dot() != null;
        }

        @Override
        public void start() {
            this.pounces = 0;
            this.pet.setFlag(TamaPet.F_CHASING, true);
        }

        @Override
        public void stop() {
            this.pet.setFlag(TamaPet.F_CHASING, false);
        }

        @Override
        public void tick() {
            Vec3 dot = dot();
            if (dot == null) {
                return;
            }
            this.pet.getLookControl().setLookAt(dot.x, dot.y, dot.z);
            double d = this.pet.position().distanceTo(dot);
            if (d > 1.4) {
                this.pet.getNavigation().moveTo(dot.x, dot.y, dot.z, 1.45);
            } else {
                this.pet.getNavigation().stop();
            }
            if (this.pounceCooldown > 0) {
                this.pounceCooldown--;
            } else if (d < 2.2 && this.pet.onGround()) {
                this.pounceCooldown = 18 + this.pet.getRandom().nextInt(10);
                this.pet.playAction(PetAction.POUNCE);
                Vec3 dir = dot.subtract(this.pet.position()).normalize().scale(0.3);
                this.pet.setDeltaMovement(dir.x, 0.38, dir.z);
                if (this.pounces++ < 15) {
                    this.pet.needs().add(Need.FUN, 2.5F);
                    this.pet.needs().add(Need.ENERGY, -0.6F);
                }
            }
        }
    }

    static final class FetchGoal extends Goal {
        private final TamaPet pet;
        private @Nullable ItemEntity ball;
        private int timer;

        FetchGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            if (busy(this.pet) || !this.pet.getCarried().isEmpty() && this.pet.getOwner() == null) {
                return false;
            }
            if (!this.pet.getCarried().isEmpty()) {
                return true;      // bring back what we hold
            }
            List<ItemEntity> balls = this.pet.level().getEntitiesOfClass(ItemEntity.class, this.pet.getBoundingBox().inflate(16, 6, 16),
                    e -> e.getItem().is(ModItems.SQUEAKY_BALL) && e.onGround());
            if (balls.isEmpty()) {
                return false;
            }
            this.ball = balls.get(0);
            return true;
        }

        @Override
        public boolean canContinueToUse() {
            return this.timer < 600 && !this.pet.isOrderedToSit() && this.pet.getTarget() == null
                    && (this.ball != null && this.ball.isAlive() || !this.pet.getCarried().isEmpty());
        }

        @Override
        public void start() {
            this.timer = 0;
        }

        @Override
        public void stop() {
            this.ball = null;
            if (!this.pet.getCarried().isEmpty() && this.pet.level() instanceof ServerLevel level) {
                // drop it where we are
                ItemEntity drop = new ItemEntity(level, this.pet.getX(), this.pet.getY() + 0.3, this.pet.getZ(), this.pet.getCarried().copy());
                level.addFreshEntity(drop);
                this.pet.setCarried(ItemStack.EMPTY);
            }
        }

        @Override
        public void tick() {
            this.timer++;
            if (this.pet.getCarried().isEmpty()) {
                if (this.ball == null || !this.ball.isAlive()) {
                    return;
                }
                this.pet.getLookControl().setLookAt(this.ball);
                this.pet.getNavigation().moveTo(this.ball, 1.4);
                if (this.pet.distanceToSqr(this.ball) < 2.2) {
                    ItemStack st = this.ball.getItem();
                    this.pet.setCarried(st.split(1));
                    if (st.isEmpty()) {
                        this.ball.discard();
                    }
                    this.pet.playSound(ModSounds.TOY_SQUEAK, 0.9F, 1.2F);
                    this.ball = null;
                }
                return;
            }
            LivingEntity owner = this.pet.getOwner();
            if (owner == null) {
                return;
            }
            this.pet.getLookControl().setLookAt(owner);
            this.pet.getNavigation().moveTo(owner, 1.3);
            if (this.pet.distanceToSqr(owner) < 4.0) {
                ItemStack carried = this.pet.getCarried().copy();
                this.pet.setCarried(ItemStack.EMPTY);
                if (!(owner instanceof Player p) || !p.getInventory().add(carried)) {
                    this.pet.spawnAtLocation((ServerLevel) this.pet.level(), carried);
                }
                this.pet.playAction(PetAction.CELEBRATE);
                this.pet.playSound(ModSounds.PET_CELEBRATE, 0.8F, this.pet.getVoicePitch());
                this.pet.needs().add(Need.FUN, 14);
                this.pet.needs().add(Need.ENERGY, -2);
                this.pet.needs().addBond(0.8F);
                this.timer = 10000;
            }
        }
    }

    // =====================================================================================
    // playground / bowl / bath / house

    static final class UseBlockGoal extends Goal {
        enum Use { EAT, BATH, BOUNCE, WHEEL, SCRATCH, SHELTER }

        private final TamaPet pet;
        private @Nullable Use use;
        private @Nullable BlockPos pos;
        private int timer;
        private int arrivedTicks;
        private int nextCheck = 60;

        UseBlockGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK, Flag.JUMP));
        }

        @Override
        public boolean canUse() {
            if (!this.pet.isTame() || busy(this.pet) || --this.nextCheck > 0) {
                return false;
            }
            this.nextCheck = 60 + this.pet.getRandom().nextInt(60);
            PetNeeds n = this.pet.needs();
            LivingEntity owner = this.pet.getOwner();
            ServerLevel level = (ServerLevel) this.pet.level();
            boolean wet = level.isRaining() && level.canSeeSky(this.pet.blockPosition());
            if ((level.isThundering() || wet) && pick(Use.SHELTER, st -> st.getBlock() instanceof PetHouseBlock, owner)) return true;
            if (n.hunger < 55 && pick(Use.EAT, st -> st.getBlock() instanceof FoodBowlBlock && st.getValue(FoodBowlBlock.FILL) > 0, owner)) return true;
            if (n.hygiene < 50 && pick(Use.BATH, st -> st.getBlock() instanceof PetBathBlock && st.getValue(PetBathBlock.FILLED), owner)) return true;
            if (n.fun < 65 && n.energy > 20) {
                int r = this.pet.getRandom().nextInt(3);
                Use[] order = r == 0 ? new Use[]{Use.WHEEL, Use.BOUNCE, Use.SCRATCH}
                        : r == 1 ? new Use[]{Use.BOUNCE, Use.SCRATCH, Use.WHEEL} : new Use[]{Use.SCRATCH, Use.WHEEL, Use.BOUNCE};
                for (Use u : order) {
                    Predicate<BlockState> p = switch (u) {
                        case WHEEL -> st -> st.getBlock() instanceof RunningWheelBlock;
                        case BOUNCE -> st -> st.getBlock() instanceof BouncyMushroomBlock;
                        default -> st -> st.getBlock() instanceof ScratchingPostBlock;
                    };
                    if (pick(u, p, owner)) return true;
                }
            }
            return false;
        }

        private boolean pick(Use use, Predicate<BlockState> test, @Nullable LivingEntity owner) {
            BlockPos found = BlockSearch.nearest(this.pet, 12, 3, test);
            if (found == null) {
                return false;
            }
            // a following pet only plays with things near its owner
            if (this.pet.mode() == TamaPet.Mode.FOLLOW && owner != null && !found.closerToCenterThan(owner.position(), 10)) {
                return false;
            }
            this.use = use;
            this.pos = found;
            return true;
        }

        @Override
        public void start() {
            this.timer = 0;
            this.arrivedTicks = 0;
            moveNear();
        }

        private void moveNear() {
            if (this.pos != null) {
                this.pet.getNavigation().moveTo(this.pos.getX() + 0.5, this.pos.getY(), this.pos.getZ() + 0.5, 1.1);
            }
        }

        @Override
        public boolean canContinueToUse() {
            if (this.pos == null || this.use == null || this.pet.getTarget() != null || this.pet.isOrderedToSit() || this.timer > 600) {
                return false;
            }
            if (this.use == Use.SHELTER) {
                ServerLevel level = (ServerLevel) this.pet.level();
                return level.isRaining() || level.isThundering();
            }
            return this.arrivedTicks < duration();
        }

        private int duration() {
            return switch (this.use) {
                case EAT -> 45;
                case BATH -> 90;
                case BOUNCE -> 110;
                case WHEEL -> 170;
                case SCRATCH -> 90;
                case SHELTER -> 2000;
            };
        }

        @Override
        public void tick() {
            this.timer++;
            if (this.pos == null || this.use == null) {
                return;
            }
            BlockState st = this.pet.level().getBlockState(this.pos);
            Vec3 c = Vec3.atBottomCenterOf(this.pos);
            this.pet.getLookControl().setLookAt(c.x, c.y + 0.4, c.z);
            boolean inside = this.use == Use.BATH || this.use == Use.WHEEL || this.use == Use.SHELTER || this.use == Use.BOUNCE;
            double close = inside ? 1.0 : 1.9;
            if (this.arrivedTicks == 0 && this.pet.position().distanceTo(c) > close + 0.6) {
                if (this.timer % 20 == 0) {
                    moveNear();
                }
                if (this.timer > 200) {
                    this.timer = 10000;   // give up
                }
                return;
            }
            if (this.arrivedTicks == 0) {
                this.pet.getNavigation().stop();
                if (inside) {
                    double y = this.use == Use.BOUNCE ? this.pos.getY() + 0.65 : this.pos.getY() + 0.1;
                    float yaw = this.pet.getYRot();
                    if (this.use == Use.WHEEL && st.hasProperty(RunningWheelBlock.FACING)) {
                        yaw = st.getValue(RunningWheelBlock.FACING).toYRot();
                    }
                    this.pet.snapTo(c.x, y, c.z, yaw, 0);
                }
            }
            this.arrivedTicks++;
            ServerLevel level = (ServerLevel) this.pet.level();
            switch (this.use) {
                case EAT -> {
                    if (this.arrivedTicks == 1) {
                        if (st.getBlock() instanceof FoodBowlBlock && st.getValue(FoodBowlBlock.FILL) > 0) {
                            FoodBowlBlock.takePortion(level, this.pos, st);
                            this.pet.eat(new ItemStack(ModItems.PET_KIBBLE));
                            this.pet.needs().add(Need.HUNGER, 10);
                        } else {
                            this.arrivedTicks = 1000;
                        }
                    }
                }
                case BATH -> {
                    this.pet.setFlag(TamaPet.F_BATHING, true);
                    if (this.arrivedTicks % 10 == 0) {
                        level.sendParticles(ParticleTypes.SPLASH, c.x, this.pos.getY() + 0.7, c.z, 10, 0.3, 0.1, 0.3, 0.1);
                        level.sendParticles(ParticleTypes.BUBBLE_POP, c.x, this.pos.getY() + 0.7, c.z, 4, 0.3, 0.1, 0.3, 0.02);
                        this.pet.playSound(ModSounds.PET_SPLASH, 0.6F, 1.0F + this.pet.getRandom().nextFloat() * 0.3F);
                    }
                    if (this.arrivedTicks == duration() - 1) {
                        this.pet.needs().add(Need.HYGIENE, 100);
                        this.pet.needs().add(Need.FUN, 8);
                        this.pet.needs().addBond(0.5F);
                        this.pet.sparkle(10);
                    }
                }
                case BOUNCE -> {
                    if (this.pet.onGround() && this.arrivedTicks % 14 == 0) {
                        this.pet.setDeltaMovement(0, 0.62, 0);
                        this.pet.playAction(PetAction.BOUNCE);
                        BouncyMushroomBlock.squish(level, this.pos);
                        this.pet.needs().add(Need.FUN, 3.5F);
                        this.pet.needs().add(Need.ENERGY, -0.8F);
                    }
                }
                case WHEEL -> {
                    this.pet.setFlag(TamaPet.F_RUNNING, true);
                    this.pet.setPos(c.x, this.pos.getY() + 0.1, c.z);
                    BlockState wheel = level.getBlockState(this.pos);
                    if (wheel.hasProperty(RunningWheelBlock.FACING)) {
                        // run across the axle, like a hamster
                        float yaw = wheel.getValue(RunningWheelBlock.FACING).toYRot();
                        this.pet.setYRot(yaw);
                        this.pet.setYBodyRot(yaw);
                        this.pet.setYHeadRot(yaw);
                        this.pet.getNavigation().stop();
                    }
                    RunningWheelBlock.setRunning(level, this.pos, true);
                    if (this.arrivedTicks % 10 == 0) {
                        this.pet.needs().add(Need.FUN, 2.0F);
                        this.pet.needs().add(Need.ENERGY, -0.7F);
                    }
                }
                case SCRATCH -> {
                    if (this.arrivedTicks % 40 == 1) {
                        this.pet.playAction(PetAction.SCRATCH);
                        level.playSound(null, this.pos, net.minecraft.sounds.SoundEvents.WOOL_HIT, SoundSource.BLOCKS, 0.6F, 1.2F);
                        this.pet.needs().add(Need.FUN, 9);
                    }
                }
                case SHELTER -> {
                    this.pet.setInSittingPose(true);
                    if (level.isDarkOutside() && this.pet.needs().energy < 80) {
                        this.pet.setSleeping(true);
                    }
                }
            }
        }

        @Override
        public void stop() {
            if (this.use == Use.WHEEL && this.pos != null) {
                RunningWheelBlock.setRunning((ServerLevel) this.pet.level(), this.pos, false);
                this.pet.needs().addBond(0.5F);
            }
            if (this.use == Use.BATH) {
                this.pet.setFlag(TamaPet.F_BATHING, false);
                this.pet.setDeltaMovement(0, 0.45, 0);
                this.pet.playAction(PetAction.SHAKE);
                this.pet.playSound(ModSounds.PET_SHAKE, 0.7F, 1.0F);
            }
            if (this.use == Use.SHELTER) {
                this.pet.setInSittingPose(this.pet.isOrderedToSit());
                this.pet.wakeUp();
            }
            if (this.use == Use.BOUNCE || this.use == Use.SCRATCH || this.use == Use.WHEEL) {
                this.pet.needs().addBond(0.3F);
            }
            this.pet.setFlag(TamaPet.F_RUNNING, false);
            this.use = null;
            this.pos = null;
        }
    }

    // =====================================================================================
    // reacting to the world: music, warmth, cake, flowers, owner eating, other pets, fireworks, rain

    static final class ReactGoal extends Goal {
        enum React { DANCE, WARM, BEG_CAKE, BEG_OWNER, SNIFF, PLAYDATE, SCARED }

        private final TamaPet pet;
        private @Nullable React react;
        private @Nullable BlockPos spot;
        private @Nullable TamaPet friend;
        private int timer;
        private int nextScan = 40;
        private boolean wasWet;

        ReactGoal(TamaPet pet) {
            this.pet = pet;
            setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
        }

        @Override
        public boolean canUse() {
            shakeOffWater();
            if (this.pet.isSleeping() || this.pet.getTarget() != null || --this.nextScan > 0) {
                return false;
            }
            this.nextScan = 40 + this.pet.getRandom().nextInt(30);
            ServerLevel level = (ServerLevel) this.pet.level();
            LivingEntity owner = this.pet.getOwner();

            if (level.isThundering() && level.canSeeSky(this.pet.blockPosition()) && this.pet.isTame()
                    && this.pet.species() != PetSpecies.EMBER_PUP) {
                this.react = React.SCARED;
                return true;
            }
            BlockPos juke = BlockSearch.nearest(this.pet, 7, 3, st -> st.is(Blocks.JUKEBOX),
                    p -> level.getBlockEntity(p) instanceof JukeboxBlockEntity j && j.getSongPlayer().isPlaying());
            if (juke != null) {
                this.react = React.DANCE;
                this.spot = juke;
                return true;
            }
            if (this.pet.isOrderedToSit()) {
                return false;
            }
            if (owner != null && owner.isUsingItem() && owner.getUseItem().has(DataComponents.FOOD) && this.pet.distanceToSqr(owner) < 36) {
                this.react = React.BEG_OWNER;
                return true;
            }
            if (this.pet.species() != PetSpecies.FROST_PENGUIN && (level.isDarkOutside() || this.pet.needs().energy < 60)) {
                BlockPos fire = BlockSearch.nearest(this.pet, 6, 2, st -> st.getBlock() instanceof CampfireBlock && st.getValue(CampfireBlock.LIT));
                if (fire != null && this.pet.getRandom().nextInt(2) == 0) {
                    this.react = React.WARM;
                    this.spot = fire;
                    return true;
                }
            }
            BlockPos cake = BlockSearch.nearest(this.pet, 6, 2, st -> st.getBlock() instanceof CakeBlock);
            if (cake != null && this.pet.getRandom().nextInt(3) == 0) {
                this.react = React.BEG_CAKE;
                this.spot = cake;
                return true;
            }
            if (this.pet.getRandom().nextInt(5) == 0) {
                BlockPos flower = BlockSearch.nearest(this.pet, 5, 2, st -> st.is(BlockTags.FLOWERS) || st.is(BlockTags.SMALL_FLOWERS));
                if (flower != null) {
                    this.react = React.SNIFF;
                    this.spot = flower;
                    return true;
                }
            }
            if (this.pet.isTame() && this.pet.getRandom().nextInt(6) == 0) {
                List<TamaPet> pets = level.getEntitiesOfClass(TamaPet.class, this.pet.getBoundingBox().inflate(8),
                        p -> p != this.pet && p.isTame() && !p.isSleeping() && !p.isOrderedToSit());
                if (!pets.isEmpty()) {
                    this.react = React.PLAYDATE;
                    this.friend = pets.get(this.pet.getRandom().nextInt(pets.size()));
                    return true;
                }
            }
            List<FireworkRocketEntity> rockets = level.getEntitiesOfClass(FireworkRocketEntity.class, this.pet.getBoundingBox().inflate(24));
            if (!rockets.isEmpty()) {
                this.pet.playAction(PetAction.LOOK_UP);
                this.pet.needs().add(Need.FUN, 3);
            }
            return false;
        }

        private void shakeOffWater() {
            boolean wet = this.pet.isInWaterOrRain();
            if (this.wasWet && !wet && this.pet.onGround() && !this.pet.hasFlag(TamaPet.F_BATHING)
                    && this.pet.species().gait() != PetSpecies.Gait.SWIM) {
                this.pet.playAction(PetAction.SHAKE);
                this.pet.playSound(ModSounds.PET_SHAKE, 0.6F, 1.0F);
                ((ServerLevel) this.pet.level()).sendParticles(ParticleTypes.SPLASH, this.pet.getX(), this.pet.getY() + 0.5, this.pet.getZ(),
                        16, 0.3, 0.2, 0.3, 0.1);
            }
            this.wasWet = wet;
        }

        @Override
        public void start() {
            this.timer = 0;
            switch (this.react) {
                case DANCE -> this.pet.setFlag(TamaPet.F_DANCING, true);
                case SCARED -> {
                    this.pet.setFlag(TamaPet.F_SCARED, true);
                    this.pet.playSound(ModSounds.PET_SCARED, 0.6F, this.pet.getVoicePitch());
                }
                case BEG_OWNER, BEG_CAKE -> this.pet.setFlag(TamaPet.F_BEGGING, true);
                default -> {
                }
            }
        }

        @Override
        public boolean canContinueToUse() {
            if (this.react == null || this.pet.getTarget() != null || this.pet.isSleeping()) {
                return false;
            }
            ServerLevel level = (ServerLevel) this.pet.level();
            return switch (this.react) {
                case DANCE -> this.spot != null && level.getBlockEntity(this.spot) instanceof JukeboxBlockEntity j
                        && j.getSongPlayer().isPlaying() && this.pet.blockPosition().closerThan(this.spot, 10);
                case SCARED -> level.isThundering() && this.timer < 400;
                case BEG_OWNER -> this.pet.getOwner() != null && this.pet.getOwner().isUsingItem() && this.timer < 200;
                case WARM -> this.timer < 400 && !level.isRaining() && !this.pet.isOrderedToSit();
                case BEG_CAKE -> this.timer < 120;
                case SNIFF -> this.timer < 80;
                case PLAYDATE -> this.friend != null && this.friend.isAlive() && this.timer < 160;
            };
        }

        @Override
        public void tick() {
            this.timer++;
            ServerLevel level = (ServerLevel) this.pet.level();
            switch (this.react) {
                case DANCE -> {
                    this.pet.getNavigation().stop();
                    if (this.timer % 25 == 0) {
                        level.sendParticles(ParticleTypes.NOTE, this.pet.getX(), this.pet.getY() + this.pet.getBbHeight() + 0.3, this.pet.getZ(),
                                1, 0.2, 0.0, 0.2, 1.0);
                        this.pet.needs().add(Need.FUN, 1.2F);
                    }
                }
                case SCARED -> {
                    LivingEntity owner = this.pet.getOwner();
                    if (owner != null && this.pet.distanceToSqr(owner) > 5) {
                        this.pet.getNavigation().moveTo(owner, 1.3);
                    }
                    if (this.timer % 40 == 0) {
                        level.sendParticles(ModParticles.SWEAT, this.pet.getX(), this.pet.getY() + this.pet.getBbHeight(), this.pet.getZ(), 1, 0.2, 0.0, 0.2, 0.0);
                    }
                }
                case BEG_OWNER -> {
                    LivingEntity owner = this.pet.getOwner();
                    if (owner != null) {
                        this.pet.getLookControl().setLookAt(owner);
                        if (this.pet.distanceToSqr(owner) > 4) {
                            this.pet.getNavigation().moveTo(owner, 1.1);
                        } else {
                            this.pet.getNavigation().stop();
                        }
                    }
                }
                case WARM, BEG_CAKE, SNIFF -> {
                    if (this.spot == null) {
                        return;
                    }
                    Vec3 c = Vec3.atCenterOf(this.spot);
                    this.pet.getLookControl().setLookAt(c.x, c.y, c.z);
                    if (this.pet.position().distanceTo(c) > 2.0) {
                        this.pet.getNavigation().moveTo(c.x, c.y, c.z, 1.0);
                    } else {
                        this.pet.getNavigation().stop();
                        if (this.react == React.WARM) {
                            this.pet.setFlag(TamaPet.F_WARMING, true);
                            if (this.timer % 20 == 0) {
                                this.pet.needs().add(Need.ENERGY, 0.6F);
                                this.pet.needs().add(Need.FUN, 0.4F);
                            }
                        } else if (this.react == React.SNIFF && this.pet.currentAction() == null && this.timer % 40 == 1) {
                            this.pet.playAction(PetAction.SNIFF);
                            level.sendParticles(ParticleTypes.HAPPY_VILLAGER, c.x, c.y, c.z, 3, 0.2, 0.2, 0.2, 0.0);
                            this.pet.needs().add(Need.FUN, 2);
                        } else if (this.react == React.BEG_CAKE) {
                            this.pet.setFlag(TamaPet.F_BEGGING, true);
                        }
                    }
                }
                case PLAYDATE -> {
                    if (this.friend == null) {
                        return;
                    }
                    this.pet.getLookControl().setLookAt(this.friend);
                    if (this.pet.distanceToSqr(this.friend) > 3) {
                        this.pet.getNavigation().moveTo(this.friend, 1.35);
                    } else if (this.timer % 20 == 0) {
                        this.pet.playAction(this.pet.getRandom().nextBoolean() ? PetAction.POUNCE : PetAction.PLAY);
                        this.pet.needs().add(Need.FUN, 4);
                        this.friend.needs().add(Need.FUN, 2);
                        Vec3 away = this.pet.position().subtract(this.friend.position()).normalize().scale(0.35);
                        this.pet.setDeltaMovement(away.x, 0.3, away.z);
                    }
                }
            }
        }

        @Override
        public void stop() {
            this.pet.setFlag(TamaPet.F_DANCING | TamaPet.F_SCARED | TamaPet.F_BEGGING | TamaPet.F_WARMING, false);
            this.react = null;
            this.spot = null;
            this.friend = null;
        }
    }
}
