package net.kasax.tamagotchi.pet;

import java.util.List;
import java.util.Optional;
import net.kasax.tamagotchi.pet.PetNeeds.Mood;
import net.kasax.tamagotchi.pet.PetNeeds.Need;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.BlockItemTags;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.TagKey;
import net.minecraft.util.Mth;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.ExperienceOrb;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.throwableitemprojectile.Snowball;
import net.minecraft.world.item.BoneMealItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.LevelEvent;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

/** The ten special talents, and how each species fights. */
public final class Talents {
    private Talents() {
    }

    // =====================================================================================
    // passive talents (server tick)

    public static void tick(TamaPet pet, ServerLevel level) {
        if (!pet.isTame() || pet.getOwner() == null || pet.isSleeping()) {
            if (pet.species() == PetSpecies.FROST_PENGUIN) {
                pet.setFlag(TamaPet.F_SLIDING, false);
            }
            return;
        }
        LivingEntity owner = pet.getOwner();
        boolean near12 = owner.level() == level && pet.distanceToSqr(owner) < 12 * 12;
        switch (pet.species()) {
            case JUNGLE_DRAGON -> greenThumb(pet, level);
            case TIDE_DRAGON -> {
                if (near12 && owner.isInWater() && pet.tickCount % 40 == 0 && pet.moodAllowsTalent()) {
                    owner.addEffect(new MobEffectInstance(MobEffects.WATER_BREATHING, 300, 0, true, false, true));
                    owner.addEffect(new MobEffectInstance(MobEffects.DOLPHINS_GRACE, 80, 0, true, false, true));
                    if (pet.talentReady()) {
                        pet.startTalentCooldown(20 * 30);
                        pet.playAction(PetAction.TALENT);
                        level.playSound(null, owner.blockPosition(), ModSounds.TALENT_BLESSING, SoundSource.NEUTRAL, 0.8F, 1.0F);
                        level.sendParticles(ParticleTypes.BUBBLE, owner.getX(), owner.getY() + 1, owner.getZ(), 20, 0.4, 0.6, 0.4, 0.1);
                    }
                }
            }
            case FROST_PENGUIN -> {
                BlockState below = level.getBlockState(pet.blockPosition().below());
                boolean slippery = below.is(BlockTags.ICE) || below.is(Blocks.SNOW_BLOCK) || level.getBlockState(pet.blockPosition()).is(Blocks.SNOW);
                pet.setFlag(TamaPet.F_SLIDING, slippery && pet.getDeltaMovement().horizontalDistanceSqr() > 0.004);
                if (pet.mode() == TamaPet.Mode.FOLLOW && near12 && pet.moodAllowsTalent() && pet.tickCount % 2 == 0) {
                    if (owner.onGround()) {
                        freezeAround(level, owner.blockPosition(), 2);
                    }
                    if (pet.onGround()) {
                        freezeAround(level, pet.blockPosition(), 1);
                    }
                }
            }
            case EMBER_PUP -> {
                if (pet.tickCount % 10 == 0 && pet.distanceToSqr(owner) < 16 * 16 && (owner.isOnFire() || owner.isInLava())
                        && pet.talentReady() && pet.moodAllowsTalent()) {
                    pet.startTalentCooldown(20 * 60);
                    owner.addEffect(new MobEffectInstance(MobEffects.FIRE_RESISTANCE, 20 * 12, 0));
                    owner.clearFire();
                    pet.playAction(PetAction.TALENT);
                    level.playSound(null, owner.blockPosition(), ModSounds.TALENT_WARM, SoundSource.NEUTRAL, 1.0F, 1.0F);
                    level.sendParticles(ParticleTypes.FLAME, owner.getX(), owner.getY() + 1, owner.getZ(), 30, 0.5, 0.8, 0.5, 0.02);
                    message(owner, "message.tamagotchi.talent.warm", pet);
                }
            }
            case SCULK_WISP -> {
                if (pet.tickCount % 20 == 0 && pet.talentReady() && pet.moodAllowsTalent() && pet.distanceToSqr(owner) < 24 * 24) {
                    List<LivingEntity> foes = level.getEntitiesOfClass(LivingEntity.class, pet.getBoundingBox().inflate(20),
                            e -> e instanceof Enemy && e.isAlive());
                    if (!foes.isEmpty()) {
                        pet.startTalentCooldown(20 * 15);
                        pet.playAction(PetAction.TALENT);
                        for (LivingEntity e : foes) {
                            e.addEffect(new MobEffectInstance(MobEffects.GLOWING, 20 * 7, 0, false, false));
                        }
                        level.sendParticles(ModParticles.SONAR, pet.getX(), pet.getY() + 0.6, pet.getZ(), 1, 0, 0, 0, 0);
                        level.playSound(null, pet.blockPosition(), ModSounds.TALENT_PING, SoundSource.NEUTRAL, 1.0F, 1.0F);
                    }
                }
            }
            case VOID_KITTEN -> itemMagnet(pet, level, owner);
            case PEBBLE_GOLEM -> oreSniffer(pet, level, owner);
            case HEX_TOAD -> brewBuddy(pet, level, owner);
            case MIMIC -> treasureBelly(pet, level, owner);
            default -> {
            }
        }
    }

    private static void message(LivingEntity owner, String key, TamaPet pet, Object... extra) {
        if (owner instanceof Player p) {
            Object[] args = new Object[extra.length + 1];
            args[0] = pet.getName();
            System.arraycopy(extra, 0, args, 1, extra.length);
            p.sendOverlayMessage(Component.translatable(key, args).withStyle(ChatFormatting.AQUA));
        }
    }

    private static void greenThumb(TamaPet pet, ServerLevel level) {
        if (pet.tickCount % 40 != 0 || !pet.talentReady() || !pet.moodAllowsTalent()) {
            return;
        }
        int grown = 0;
        BlockPos o = pet.blockPosition();
        for (int i = 0; i < 40 && grown < 3; i++) {
            BlockPos p = o.offset(pet.getRandom().nextInt(11) - 5, pet.getRandom().nextInt(5) - 2, pet.getRandom().nextInt(11) - 5);
            BlockState st = level.getBlockState(p);
            boolean plant = st.is(BlockTags.CROPS) || st.is(BlockTags.SAPLINGS) || st.is(Blocks.SWEET_BERRY_BUSH) || st.is(Blocks.COCOA)
                    || st.is(Blocks.MELON_STEM) || st.is(Blocks.PUMPKIN_STEM);
            if (plant && BoneMealItem.growCrop(new ItemStack(Items.BONE_MEAL), level, p)) {
                level.levelEvent(LevelEvent.PARTICLES_AND_SOUND_PLANT_GROWTH, p, 15);
                grown++;
            }
        }
        if (grown > 0) {
            pet.startTalentCooldown(20 * 20);
            pet.playAction(PetAction.TALENT);
            level.playSound(null, pet.blockPosition(), ModSounds.TALENT_GROW, SoundSource.NEUTRAL, 0.8F, 1.0F);
            level.sendParticles(ModParticles.LEAF, pet.getX(), pet.getY() + 0.8, pet.getZ(), 8, 0.5, 0.3, 0.5, 0.02);
        } else {
            pet.startTalentCooldown(20 * 5);
        }
    }

    private static void freezeAround(ServerLevel level, BlockPos feet, int r) {
        BlockState frosted = Blocks.FROSTED_ICE.defaultBlockState();
        BlockPos center = feet.below();
        for (BlockPos p : BlockPos.betweenClosed(center.offset(-r, 0, -r), center.offset(r, 0, r))) {
            if (p.distToCenterSqr(center.getX() + 0.5, center.getY() + 0.5, center.getZ() + 0.5) > (r + 0.5) * (r + 0.5)) {
                continue;
            }
            BlockState st = level.getBlockState(p);
            if (st.is(Blocks.WATER) && st.getFluidState().isSource() && level.getBlockState(p.above()).isAir()
                    && frosted.canSurvive(level, p) && level.isUnobstructed(frosted, p, net.minecraft.world.phys.shapes.CollisionContext.empty())) {
                level.setBlockAndUpdate(p, frosted);
                level.scheduleTick(p.immutable(), Blocks.FROSTED_ICE, Mth.nextInt(level.getRandom(), 60, 120));
            }
        }
    }

    private static void itemMagnet(TamaPet pet, ServerLevel level, LivingEntity owner) {
        if (pet.tickCount % 10 != 0 || !pet.moodAllowsTalent()) {
            return;
        }
        List<ItemEntity> items = level.getEntitiesOfClass(ItemEntity.class, pet.getBoundingBox().inflate(6, 3, 6),
                e -> e.isAlive() && !e.hasPickUpDelay() && e.getAge() > 30 && e.getOwner() != owner);
        int moved = 0;
        for (ItemEntity it : items) {
            if (moved >= 3) {
                break;
            }
            ItemStack stack = it.getItem();
            level.sendParticles(ParticleTypes.PORTAL, it.getX(), it.getY() + 0.2, it.getZ(), 8, 0.2, 0.2, 0.2, 0.3);
            if (pet.storageSlots() > 0 && pet.canStore(stack)) {
                ItemStack rest = pet.store(stack.copy());
                if (rest.isEmpty()) {
                    it.discard();
                } else {
                    it.setItem(rest);
                }
            } else if (owner.distanceToSqr(it) > 4) {
                it.teleportTo(owner.getX(), owner.getY() + 0.2, owner.getZ());
                it.setDeltaMovement(Vec3.ZERO);
            } else {
                continue;
            }
            moved++;
        }
        if (moved > 0) {
            level.playSound(null, pet.blockPosition(), ModSounds.TALENT_MAGNET, SoundSource.NEUTRAL, 0.5F, 1.2F);
            if (pet.currentAction() == null) {
                pet.playAction(PetAction.TALENT);
            }
        }
    }

    private static final List<TagKey<Block>> ORES = List.of(BlockItemTags.DIAMOND_ORES.block(), BlockItemTags.EMERALD_ORES.block(),
            BlockTags.GOLD_ORES, BlockItemTags.LAPIS_ORES.block(), BlockItemTags.REDSTONE_ORES.block(), BlockTags.IRON_ORES,
            BlockTags.COPPER_ORES, BlockItemTags.COAL_ORES.block());

    private static void oreSniffer(TamaPet pet, ServerLevel level, LivingEntity owner) {
        if (pet.tickCount % 20 != 0 || !pet.talentReady() || !pet.moodAllowsTalent() || pet.distanceToSqr(owner) > 12 * 12
                || level.canSeeSky(owner.blockPosition())) {
            return;
        }
        BlockPos o = pet.blockPosition();
        BlockPos best = null;
        int bestRank = ORES.size();
        double bestD = Double.MAX_VALUE;
        BlockPos.MutableBlockPos m = new BlockPos.MutableBlockPos();
        int r = 10;
        for (int dx = -r; dx <= r; dx++) {
            for (int dy = -r; dy <= r; dy++) {
                for (int dz = -r; dz <= r; dz++) {
                    m.set(o.getX() + dx, o.getY() + dy, o.getZ() + dz);
                    BlockState st = level.getBlockState(m);
                    if (st.isAir() || st.is(Blocks.STONE) || st.is(Blocks.DEEPSLATE)) {
                        continue;
                    }
                    for (int rank = 0; rank < ORES.size(); rank++) {
                        if (st.is(ORES.get(rank))) {
                            double d = dx * dx + dy * dy + dz * dz;
                            if (rank < bestRank || rank == bestRank && d < bestD) {
                                best = m.immutable();
                                bestRank = rank;
                                bestD = d;
                            }
                            break;
                        }
                    }
                }
            }
        }
        pet.startTalentCooldown(best == null ? 20 * 10 : 20 * 30);
        if (best == null) {
            return;
        }
        pet.playAction(PetAction.SNIFF);
        pet.getLookControl().setLookAt(best.getX() + 0.5, best.getY() + 0.5, best.getZ() + 0.5);
        Vec3 from = pet.position().add(0, pet.getBbHeight() * 0.6, 0);
        Vec3 to = Vec3.atCenterOf(best);
        Vec3 step = to.subtract(from);
        int n = (int) Math.ceil(step.length() / 0.5);
        for (int i = 1; i <= n; i++) {
            Vec3 p = from.add(step.scale(i / (double) n));
            level.sendParticles(ModParticles.SPARKLE, p.x, p.y, p.z, 1, 0.02, 0.02, 0.02, 0.0);
        }
        level.sendParticles(ParticleTypes.WAX_OFF, to.x, to.y, to.z, 12, 0.4, 0.4, 0.4, 0.0);
        level.playSound(null, pet.blockPosition(), ModSounds.TALENT_SNIFF, SoundSource.NEUTRAL, 1.0F, 1.0F);
        message(owner, "message.tamagotchi.talent.ore", pet, level.getBlockState(best).getBlock().getName());
    }

    private static final List<Holder<MobEffect>> BREWS = List.of(MobEffects.SPEED, MobEffects.JUMP_BOOST, MobEffects.HASTE,
            MobEffects.REGENERATION, MobEffects.NIGHT_VISION, MobEffects.LUCK, MobEffects.RESISTANCE, MobEffects.FIRE_RESISTANCE);

    private static void brewBuddy(TamaPet pet, ServerLevel level, LivingEntity owner) {
        if (pet.tickCount % 20 != 0 || !pet.talentReady() || !pet.needs().mood().atLeast(Mood.HAPPY) || pet.distanceToSqr(owner) > 8 * 8) {
            return;
        }
        pet.startTalentCooldown(20 * 120);
        Holder<MobEffect> effect = BREWS.get(pet.getRandom().nextInt(BREWS.size()));
        owner.addEffect(new MobEffectInstance(effect, 20 * 60, 0));
        pet.playAction(PetAction.TALENT);
        level.playSound(null, pet.blockPosition(), ModSounds.TALENT_BREW, SoundSource.NEUTRAL, 1.0F, 1.0F);
        level.sendParticles(ParticleTypes.WITCH, owner.getX(), owner.getY() + 1.2, owner.getZ(), 16, 0.4, 0.5, 0.4, 0.05);
        message(owner, "message.tamagotchi.talent.brew", pet, effect.value().getDisplayName());
    }

    private static void treasureBelly(TamaPet pet, ServerLevel level, LivingEntity owner) {
        if (pet.tickCount % 20 != 0 || !pet.talentReady() || !pet.needs().mood().atLeast(Mood.HAPPY) || pet.distanceToSqr(owner) > 10 * 10) {
            return;
        }
        pet.startTalentCooldown(20 * 300);
        int roll = pet.getRandom().nextInt(100);
        ItemStack loot;
        if (roll < 35) loot = new ItemStack(Items.GOLD_NUGGET, 1 + pet.getRandom().nextInt(4));
        else if (roll < 58) loot = new ItemStack(Items.IRON_NUGGET, 2 + pet.getRandom().nextInt(4));
        else if (roll < 70) loot = new ItemStack(Items.LAPIS_LAZULI, 1 + pet.getRandom().nextInt(3));
        else if (roll < 80) loot = new ItemStack(Items.AMETHYST_SHARD, 1 + pet.getRandom().nextInt(2));
        else if (roll < 88) loot = new ItemStack(Items.EMERALD);
        else if (roll < 94) loot = new ItemStack(Items.GOLD_INGOT);
        else if (roll < 97) loot = new ItemStack(Items.NAME_TAG);
        else if (roll < 99) loot = new ItemStack(Items.DIAMOND);
        else loot = new ItemStack(Items.GOLDEN_APPLE);
        pet.playAction(PetAction.COUGH);
        Vec3 mouth = pet.headPos();
        ItemEntity item = new ItemEntity(level, mouth.x, mouth.y, mouth.z, loot);
        Vec3 toward = owner.position().subtract(pet.position()).normalize().scale(0.2);
        item.setDeltaMovement(toward.x, 0.25, toward.z);
        item.setPickUpDelay(10);
        level.addFreshEntity(item);
        level.playSound(null, pet.blockPosition(), ModSounds.TALENT_TREASURE, SoundSource.NEUTRAL, 1.0F, 1.0F);
        message(owner, "message.tamagotchi.talent.treasure", pet);
    }

    // =====================================================================================
    // item talents (right-click)

    /** Desert Dragon roasts raw food and smelts raw ore handed to it. */
    public static boolean handleItem(TamaPet pet, Player player, InteractionHand hand, ItemStack stack) {
        if (pet.species() != PetSpecies.DESERT_DRAGON || stack.isEmpty()) {
            return false;
        }
        if (!(pet.level() instanceof ServerLevel level)) {
            return pet.level().recipeAccess() == null || isSmeltable(stack);
        }
        SingleRecipeInput input = new SingleRecipeInput(stack.copyWithCount(1));
        Optional<RecipeHolder<SmeltingRecipe>> recipe = level.recipeAccess().getRecipeFor(RecipeType.SMELTING, input, level);
        if (recipe.isEmpty()) {
            return false;
        }
        if (!pet.moodAllowsTalent()) {
            player.sendOverlayMessage(Component.translatable("message.tamagotchi.too_sad", pet.getName()));
            return true;
        }
        ItemStack result = recipe.get().value().assemble(input);
        if (result.isEmpty()) {
            return false;
        }
        stack.consume(1, player);
        pet.playAction(PetAction.BREATH);
        level.playSound(null, pet.blockPosition(), ModSounds.TALENT_ROAST, SoundSource.NEUTRAL, 1.0F, 1.0F);
        breathLine(level, pet, player.position().add(0, 1.0, 0), ParticleTypes.FLAME, 10);
        player.getInventory().placeItemBackInInventory(result.copy(), net.minecraft.util.Prediction.SERVER_ONLY);
        float xp = recipe.get().value().experience();
        if (xp > 0) {
            ExperienceOrb.award(level, player.position(), Math.max(1, Mth.floor(xp + level.getRandom().nextFloat())));
        }
        pet.needs().add(Need.ENERGY, -0.5F);
        pet.needs().addBond(0.2F);
        return true;
    }

    private static boolean isSmeltable(ItemStack stack) {
        Item i = stack.getItem();
        return i == Items.BEEF || i == Items.PORKCHOP || i == Items.CHICKEN || i == Items.MUTTON || i == Items.RABBIT || i == Items.COD
                || i == Items.SALMON || i == Items.POTATO || i == Items.KELP || i == Items.RAW_IRON || i == Items.RAW_GOLD
                || i == Items.RAW_COPPER || i == Items.SAND || i == Items.COBBLESTONE || i == Items.CLAY_BALL;
    }

    // =====================================================================================
    // attacks

    /** Performs the species attack. Returns the cooldown in ticks. */
    public static int attack(TamaPet pet, ServerLevel level, LivingEntity target) {
        float dmg = (float) pet.getAttributeValue(Attributes.ATTACK_DAMAGE);
        pet.playSound(pet.attackSound(), 0.8F, pet.getVoicePitch());
        if (pet.isTame()) {
            pet.needs().add(Need.ENERGY, -1.0F);
        }
        Vec3 aim = target.position().add(0, target.getBbHeight() * 0.5, 0);
        switch (pet.species().attackStyle()) {
            case FIRE_BREATH -> {
                pet.playAction(PetAction.BREATH);
                breathLine(level, pet, aim, ParticleTypes.FLAME, 14);
                if (target.hurtServer(level, pet.damageSources().mobAttack(pet), dmg)) {
                    target.igniteForSeconds(3);
                }
                return 32;
            }
            case POISON_BITE -> {
                pet.playAction(PetAction.ATTACK);
                if (pet.doHurtTarget(level, target)) {
                    target.addEffect(new MobEffectInstance(MobEffects.POISON, 80, 0), pet);
                }
                level.sendParticles(ModParticles.LEAF, aim.x, aim.y, aim.z, 4, 0.2, 0.2, 0.2, 0.02);
                return 20;
            }
            case BUBBLE -> {
                pet.playAction(PetAction.BREATH);
                breathLine(level, pet, aim, ParticleTypes.BUBBLE, 16);
                level.sendParticles(ParticleTypes.BUBBLE_POP, aim.x, aim.y, aim.z, 12, 0.3, 0.3, 0.3, 0.05);
                if (target.hurtServer(level, pet.damageSources().mobAttack(pet), dmg * 0.9F)) {
                    Vec3 push = target.position().subtract(pet.position()).normalize().scale(0.9);
                    target.push(push.x, 0.25, push.z);
                }
                return 30;
            }
            case SNOWBALL -> {
                pet.playAction(PetAction.ATTACK);
                Snowball ball = new Snowball(level, pet, new ItemStack(Items.SNOWBALL));
                Vec3 d = aim.subtract(ball.position());
                ball.shoot(d.x, d.y + d.horizontalDistance() * 0.15, d.z, 1.3F, 2.0F);
                level.addFreshEntity(ball);
                if (target.hurtServer(level, pet.damageSources().mobAttack(pet), dmg)) {
                    target.addEffect(new MobEffectInstance(MobEffects.SLOWNESS, 60, 1), pet);
                    level.sendParticles(ParticleTypes.SNOWFLAKE, aim.x, aim.y, aim.z, 10, 0.3, 0.3, 0.3, 0.02);
                }
                return 24;
            }
            case BURN_BITE -> {
                pet.playAction(PetAction.ATTACK);
                if (pet.doHurtTarget(level, target)) {
                    target.igniteForSeconds(4);
                }
                return 20;
            }
            case SONIC -> {
                pet.playAction(PetAction.BREATH);
                breathLine(level, pet, aim, ParticleTypes.SCULK_CHARGE_POP, 10);
                level.sendParticles(ParticleTypes.SONIC_BOOM, aim.x, aim.y, aim.z, 1, 0, 0, 0, 0);
                target.hurtServer(level, pet.damageSources().sonicBoom(pet), dmg * 0.85F);
                return 36;
            }
            case BLINK -> {
                Vec3 behind = target.position().subtract(target.getLookAngle().multiply(1, 0, 1).normalize().scale(1.3));
                level.sendParticles(ParticleTypes.PORTAL, pet.getX(), pet.getY() + 0.4, pet.getZ(), 20, 0.3, 0.3, 0.3, 0.4);
                if (level.noCollision(pet, pet.getBoundingBox().move(behind.subtract(pet.position())))) {
                    pet.teleportTo(behind.x, behind.y, behind.z);
                    pet.getLookControl().setLookAt(target);
                }
                pet.playAction(PetAction.ATTACK);
                pet.doHurtTarget(level, target);
                return 30;
            }
            case SLAM -> {
                pet.playAction(PetAction.ATTACK);
                level.sendParticles(ParticleTypes.EXPLOSION, pet.getX(), pet.getY() + 0.2, pet.getZ(), 1, 0, 0, 0, 0);
                for (LivingEntity e : level.getEntitiesOfClass(LivingEntity.class, pet.getBoundingBox().inflate(2.5, 1, 2.5),
                        e -> e != pet && (e == target || e instanceof Enemy) && !pet.isAlliedTo(e))) {
                    if (e.hurtServer(level, pet.damageSources().mobAttack(pet), dmg)) {
                        Vec3 push = e.position().subtract(pet.position()).normalize().scale(0.7);
                        e.push(push.x, 0.3, push.z);
                    }
                }
                return 34;
            }
            case TONGUE -> {
                pet.playAction(PetAction.ATTACK);
                if (target.hurtServer(level, pet.damageSources().mobAttack(pet), dmg)) {
                    Vec3 pull = pet.position().subtract(target.position()).normalize().scale(0.55);
                    target.push(pull.x, 0.15, pull.z);
                    target.addEffect(new MobEffectInstance(MobEffects.WEAKNESS, 80, 0), pet);
                }
                return 28;
            }
            case CHOMP -> {
                pet.playAction(PetAction.ATTACK);
                pet.doHurtTarget(level, target);
                return 24;
            }
        }
        return 20;
    }

    private static void breathLine(ServerLevel level, TamaPet pet, Vec3 to, ParticleOptions particle, int count) {
        Vec3 from = pet.headPos();
        Vec3 d = to.subtract(from);
        for (int i = 0; i < count; i++) {
            double t = (i + level.getRandom().nextDouble()) / count;
            Vec3 p = from.add(d.scale(t));
            level.sendParticles(particle, p.x, p.y, p.z, 1, 0.06 + t * 0.12, 0.06 + t * 0.12, 0.06 + t * 0.12, 0.01);
        }
    }
}
