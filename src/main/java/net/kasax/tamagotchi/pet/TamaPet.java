package net.kasax.tamagotchi.pet;

import java.util.List;
import java.util.UUID;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.item.TamaEggItem;
import net.kasax.tamagotchi.menu.PetMenu;
import net.kasax.tamagotchi.pet.PetNeeds.Mood;
import net.kasax.tamagotchi.pet.PetNeeds.Need;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.NonNullList;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.Mth;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.AgeableMob;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.navigation.AmphibiousPathNavigation;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.animal.Animal;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.pathfinder.PathType;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The pet. One class for all ten species; {@link #species()} comes from the entity type.
 *
 * <p>Server side it owns the Tamagotchi needs, the backpack inventory, the golden-apple snack
 * pouch, the command mode and the faint-into-egg rule. Client side it only keeps animation clocks:
 * one-shot {@link PetAction}s arrive as entity events, looping states as synced flags.
 */
public class TamaPet extends TamableAnimal {
    // ---- synced flags (DATA_FLAGS) ----
    public static final int F_BACKPACK = 1;
    public static final int F_SLEEPING = 1 << 1;
    public static final int F_DANCING = 1 << 2;
    public static final int F_SCARED = 1 << 3;
    public static final int F_BEGGING = 1 << 4;
    public static final int F_AGGRESSIVE = 1 << 5;
    public static final int F_WANDER = 1 << 6;
    public static final int F_WARMING = 1 << 7;
    public static final int F_BATHING = 1 << 8;
    public static final int F_RUNNING = 1 << 9;
    public static final int F_SLIDING = 1 << 10;
    public static final int F_CHASING = 1 << 11;

    private static final EntityDataAccessor<Integer> DATA_NEEDS = SynchedEntityData.defineId(TamaPet.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Integer> DATA_STATE = SynchedEntityData.defineId(TamaPet.class, EntityDataSerializers.INT);
    private static final EntityDataAccessor<Byte> DATA_BOND = SynchedEntityData.defineId(TamaPet.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<Byte> DATA_SNACKS = SynchedEntityData.defineId(TamaPet.class, EntityDataSerializers.BYTE);
    private static final EntityDataAccessor<ItemStack> DATA_CARRIED = SynchedEntityData.defineId(TamaPet.class, EntityDataSerializers.ITEM_STACK);

    public static final int BACKPACK_SLOTS = 27;
    public static final int MAX_SNACKS = 16;

    private final PetSpecies species;
    private final PetNeeds needs = new PetNeeds();
    /** Slots 0..26 = belly (mimic only) or backpack, 27..53 = the mimic's backpack. */
    private final SimpleContainer inventory = new SimpleContainer(BACKPACK_SLOTS * 2);
    private int snacks;
    private @Nullable BlockPos home;
    private int ticksToNeeds;
    private int emoteCooldown = 100;
    private int petCooldown;
    private int talentCooldown = 200;
    private final int[] beepCooldown = new int[5];
    private int serverActionTicks;
    private @Nullable PetAction serverAction;
    private int lastOwnerLevel = -1;

    // ---- client animation clocks ----
    public @Nullable PetAction clientAction;
    public int clientActionStart;
    public int nextBlinkTick = 40;
    public int blinkUntil;

    public TamaPet(EntityType<? extends TamaPet> type, Level level) {
        super(type, level);
        this.species = ModEntities.speciesOf(type);
        this.setTame(false, false);
        if (this.species.fireImmune()) {
            this.setPathfindingMalus(PathType.LAVA, 8.0F);
            this.setPathfindingMalus(PathType.FIRE_IN_NEIGHBOR, 0.0F);
            this.setPathfindingMalus(PathType.FIRE, 0.0F);
        }
        if (this.species.gait() == PetSpecies.Gait.SWIM || this.species.waterBreathing()) {
            this.setPathfindingMalus(PathType.WATER, 0.0F);
        }
        if (this.species.gait() == PetSpecies.Gait.SWIM) {
            this.moveControl = new PetSwimMoveControl(this);
        }
        this.setPersistenceRequired();
    }

    public static AttributeSupplier.Builder createAttributes(PetSpecies species) {
        return Animal.createAnimalAttributes()
                .add(Attributes.MAX_HEALTH, species.maxHealth())
                .add(Attributes.MOVEMENT_SPEED, species.speed())
                .add(Attributes.ATTACK_DAMAGE, species.attackDamage())
                .add(Attributes.ARMOR, species.armor())
                .add(Attributes.FOLLOW_RANGE, 24.0)
                .add(Attributes.KNOCKBACK_RESISTANCE, species == PetSpecies.PEBBLE_GOLEM ? 0.8 : 0.0)
                .add(Attributes.SAFE_FALL_DISTANCE, species.flying() ? 64.0 : 4.0);
    }

    public PetSpecies species() {
        return this.species;
    }

    @Override
    protected PathNavigation createNavigation(Level level) {
        PetSpecies s = ModEntities.speciesOf(this.getType());
        if (s.gait() == PetSpecies.Gait.SWIM) {
            return new AmphibiousPathNavigation(this, level);
        }
        return super.createNavigation(level);
    }

    @Override
    protected void registerGoals() {
        PetGoals.register(this, this.goalSelector, this.targetSelector);
    }

    // ------------------------------------------------------------------ synced data

    @Override
    protected void defineSynchedData(SynchedEntityData.Builder builder) {
        super.defineSynchedData(builder);
        builder.define(DATA_NEEDS, this.needs.pack());
        builder.define(DATA_STATE, 0);
        builder.define(DATA_BOND, (byte) 0);
        builder.define(DATA_SNACKS, (byte) 0);
        builder.define(DATA_CARRIED, ItemStack.EMPTY);
    }

    public int syncedFlags() {
        return this.entityData.get(DATA_STATE);
    }

    public boolean hasFlag(int flag) {
        return (this.entityData.get(DATA_STATE) & flag) != 0;
    }

    public void setFlag(int flag, boolean on) {
        int cur = this.entityData.get(DATA_STATE);
        int next = on ? cur | flag : cur & ~flag;
        if (next != cur) {
            this.entityData.set(DATA_STATE, next);
        }
    }

    /** Need values as the client sees them (0..100). */
    public int syncedNeed(Need need) {
        return PetNeeds.unpack(this.entityData.get(DATA_NEEDS), need);
    }

    public float syncedMoodValue() {
        return PetNeeds.moodValue(syncedNeed(Need.HUNGER), syncedNeed(Need.FUN), syncedNeed(Need.ENERGY), syncedNeed(Need.HYGIENE));
    }

    public Mood syncedMood() {
        return isTame() ? Mood.of(syncedMoodValue()) : Mood.HAPPY;
    }

    public int syncedBond() {
        return this.entityData.get(DATA_BOND);
    }

    public int syncedSnacks() {
        return this.entityData.get(DATA_SNACKS);
    }

    public ItemStack getCarried() {
        return this.entityData.get(DATA_CARRIED);
    }

    public void setCarried(ItemStack stack) {
        this.entityData.set(DATA_CARRIED, stack);
    }

    private void syncNeeds() {
        this.entityData.set(DATA_NEEDS, this.needs.pack());
        this.entityData.set(DATA_BOND, (byte) Math.round(this.needs.bond));
    }

    // ------------------------------------------------------------------ save / load

    @Override
    protected void addAdditionalSaveData(ValueOutput output) {
        super.addAdditionalSaveData(output);
        this.needs.save(output);
        output.putBoolean("Backpack", hasBackpack());
        output.putBoolean("Wander", hasFlag(F_WANDER));
        output.putInt("Snacks", this.snacks);
        if (this.home != null) {
            output.store("Home", BlockPos.CODEC, this.home);
        }
        NonNullList<ItemStack> items = NonNullList.withSize(this.inventory.getContainerSize(), ItemStack.EMPTY);
        for (int i = 0; i < items.size(); i++) {
            items.set(i, this.inventory.getItem(i));
        }
        ContainerHelper.saveAllItems(output.child("Inventory"), items);
    }

    @Override
    protected void readAdditionalSaveData(ValueInput input) {
        super.readAdditionalSaveData(input);
        this.needs.load(input);
        setFlag(F_BACKPACK, input.getBooleanOr("Backpack", false));
        setFlag(F_WANDER, input.getBooleanOr("Wander", false));
        this.snacks = input.getIntOr("Snacks", 0);
        this.home = input.read("Home", BlockPos.CODEC).orElse(null);
        NonNullList<ItemStack> items = NonNullList.withSize(this.inventory.getContainerSize(), ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input.childOrEmpty("Inventory"), items);
        for (int i = 0; i < items.size(); i++) {
            this.inventory.setItem(i, items.get(i));
        }
        this.entityData.set(DATA_SNACKS, (byte) this.snacks);
        syncNeeds();
    }

    // ------------------------------------------------------------------ inventory

    public PetNeeds needs() {
        return this.needs;
    }

    public SimpleContainer inventory() {
        return this.inventory;
    }

    public boolean hasBackpack() {
        return hasFlag(F_BACKPACK);
    }

    /** Usable storage slots right now (belly and/or backpack). */
    public int storageSlots() {
        int n = this.species.hasBelly() ? BACKPACK_SLOTS : 0;
        return hasBackpack() ? n + BACKPACK_SLOTS : n;
    }

    /** First slot index of the backpack part. */
    public int backpackStart() {
        return this.species.hasBelly() ? BACKPACK_SLOTS : 0;
    }

    public int snacks() {
        return this.snacks;
    }

    public void setSnacks(int value) {
        this.snacks = Mth.clamp(value, 0, MAX_SNACKS);
        this.entityData.set(DATA_SNACKS, (byte) this.snacks);
    }

    /** Puts a stack into belly/backpack slots; returns what didn't fit. */
    public ItemStack store(ItemStack stack) {
        int slots = storageSlots();
        for (int i = 0; i < slots && !stack.isEmpty(); i++) {
            ItemStack cur = this.inventory.getItem(i);
            if (!cur.isEmpty() && ItemStack.isSameItemSameComponents(cur, stack) && cur.getCount() < cur.getMaxStackSize()) {
                int move = Math.min(stack.getCount(), cur.getMaxStackSize() - cur.getCount());
                cur.grow(move);
                stack.shrink(move);
            }
        }
        for (int i = 0; i < slots && !stack.isEmpty(); i++) {
            if (this.inventory.getItem(i).isEmpty()) {
                this.inventory.setItem(i, stack.copy());
                stack.setCount(0);
            }
        }
        this.inventory.setChanged();
        return stack;
    }

    public boolean canStore(ItemStack stack) {
        int slots = storageSlots();
        for (int i = 0; i < slots; i++) {
            ItemStack cur = this.inventory.getItem(i);
            if (cur.isEmpty() || ItemStack.isSameItemSameComponents(cur, stack) && cur.getCount() < cur.getMaxStackSize()) {
                return true;
            }
        }
        return false;
    }

    public void equipBackpack() {
        setFlag(F_BACKPACK, true);
        playSound(ModSounds.BACKPACK_EQUIP, 1.0F, 1.0F);
        playAction(PetAction.CELEBRATE);
    }

    /** Takes the backpack off; everything in it spills onto the ground (with the chest). */
    public void removeBackpack(boolean spill) {
        if (!hasBackpack() || !(level() instanceof ServerLevel level)) {
            return;
        }
        int start = backpackStart();
        if (spill) {
            for (int i = start; i < start + BACKPACK_SLOTS; i++) {
                ItemStack stack = this.inventory.removeItemNoUpdate(i);
                if (!stack.isEmpty()) {
                    spawnSpill(level, stack);
                }
            }
            spawnSpill(level, new ItemStack(Items.CHEST));
        }
        setFlag(F_BACKPACK, false);
        playSound(ModSounds.BACKPACK_SPILL, 1.0F, 1.0F);
        playAction(PetAction.SHAKE);
    }

    private void spawnSpill(ServerLevel level, ItemStack stack) {
        ItemEntity item = new ItemEntity(level, getX(), getY() + 0.6, getZ(), stack);
        item.setDeltaMovement(this.random.nextGaussian() * 0.12, 0.25 + this.random.nextFloat() * 0.15, this.random.nextGaussian() * 0.12);
        item.setDefaultPickUpDelay();
        level.addFreshEntity(item);
    }

    // ------------------------------------------------------------------ modes

    public enum Mode { FOLLOW, SIT, WANDER }

    public Mode mode() {
        if (isOrderedToSit()) return Mode.SIT;
        return hasFlag(F_WANDER) ? Mode.WANDER : Mode.FOLLOW;
    }

    public void setMode(Mode mode) {
        setOrderedToSit(mode == Mode.SIT);
        setInSittingPose(mode == Mode.SIT);
        setFlag(F_WANDER, mode == Mode.WANDER);
        if (mode == Mode.WANDER) {
            this.home = blockPosition();
        }
        this.navigation.stop();
        setTarget(null);
        wakeUp();
    }

    public @Nullable BlockPos home() {
        return this.home;
    }

    public void setHome(@Nullable BlockPos home) {
        this.home = home;
    }

    // ------------------------------------------------------------------ actions / animation

    /** Server: start a one-shot animation on every watching client. */
    public void playAction(PetAction action) {
        if (!level().isClientSide()) {
            this.serverAction = action;
            this.serverActionTicks = action.length;
            level().broadcastEntityEvent(this, action.eventId());
        }
    }

    /** Server: the action currently playing (goals use it to wait for an animation). */
    public @Nullable PetAction currentAction() {
        return this.serverActionTicks > 0 ? this.serverAction : null;
    }

    @Override
    public void handleEntityEvent(byte id) {
        PetAction action = PetAction.byEvent(id);
        if (action != null) {
            this.clientAction = action;
            this.clientActionStart = this.tickCount;
            if (action == PetAction.PETTED || action == PetAction.TAMED) {
                for (int i = 0; i < 5; i++) {
                    level().addParticle(ParticleTypes.HEART, getRandomX(0.6), getY() + getBbHeight() + 0.1, getRandomZ(0.6), 0, 0.05, 0);
                }
            }
            return;
        }
        super.handleEntityEvent(id);
    }

    /** Client: progress 0..1 of the playing action, or -1. */
    public float actionProgress(float partialTick) {
        if (this.clientAction == null) {
            return -1;
        }
        float t = (this.tickCount + partialTick - this.clientActionStart) / this.clientAction.length;
        if (t >= 1F || t < 0F) {
            this.clientAction = null;
            return -1;
        }
        return t;
    }

    public boolean isSleeping() {
        return hasFlag(F_SLEEPING);
    }

    public void setSleeping(boolean sleeping) {
        setFlag(F_SLEEPING, sleeping);
        if (sleeping) {
            this.navigation.stop();
        }
    }

    public void wakeUp() {
        if (isSleeping()) {
            setSleeping(false);
            playAction(PetAction.YAWN);
            playSound(ModSounds.PET_YAWN, 0.6F, getVoicePitch());
        }
    }

    // ------------------------------------------------------------------ interaction

    @Override
    public InteractionResult mobInteract(Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        boolean client = level().isClientSide();

        if (!isTame()) {
            if (stack.is(ModItems.TAMAGOTCHI_HEART)) {
                if (!client) {
                    tameBy(player);
                    stack.consume(1, player);
                }
                return InteractionResult.SUCCESS;
            }
            return super.mobInteract(player, hand);
        }
        if (!isOwnedBy(player)) {
            return InteractionResult.PASS;
        }

        // sneak + right-click: backpack on / off (or sit when there is no backpack)
        if (player.isSecondaryUseActive()) {
            if (stack.is(Items.CHEST) && !hasBackpack()) {
                if (!client) {
                    equipBackpack();
                    stack.consume(1, player);
                }
                return InteractionResult.SUCCESS;
            }
            if (stack.isEmpty()) {
                if (!client) {
                    if (hasBackpack()) {
                        removeBackpack(true);
                    } else {
                        setMode(isOrderedToSit() ? Mode.FOLLOW : Mode.SIT);
                        player.sendOverlayMessage(Component.translatable(isOrderedToSit() ? "message.tamagotchi.stay" : "message.tamagotchi.follow", getName()));
                    }
                }
                return InteractionResult.SUCCESS;
            }
        }

        if (stack.is(ModItems.TAMA_PAGER)) {
            if (player instanceof ServerPlayer sp) {
                openPetScreen(sp);
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.is(Items.GOLDEN_APPLE) || stack.is(Items.ENCHANTED_GOLDEN_APPLE)) {
            if (this.snacks >= MAX_SNACKS) {
                return InteractionResult.PASS;
            }
            if (!client) {
                setSnacks(this.snacks + 1);
                stack.consume(1, player);
                playAction(PetAction.CELEBRATE);
                playSound(ModSounds.PET_CELEBRATE, 0.8F, getVoicePitch());
                player.sendOverlayMessage(Component.translatable("message.tamagotchi.snack_stored", getName(), this.snacks));
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.is(ModItems.PET_BRUSH)) {
            if (!client) {
                groom(player);
                stack.hurtAndBreak(1, player, hand);
            }
            return InteractionResult.SUCCESS;
        }
        if (Talents.handleItem(this, player, hand, stack)) {
            return InteractionResult.SUCCESS;
        }
        if (isPetFood(stack)) {
            if (this.needs.hunger >= 98 && getHealth() >= getMaxHealth()) {
                if (!client) {
                    player.sendOverlayMessage(Component.translatable("message.tamagotchi.full", getName()));
                }
                return InteractionResult.PASS;
            }
            if (!client) {
                feedFrom(player, stack);
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.is(ModItems.SQUEAKY_BALL) || stack.is(ModItems.FEATHER_WAND)) {
            if (!client) {
                playWith(player);
            }
            return InteractionResult.SUCCESS;
        }
        if (stack.isEmpty()) {
            if (!client) {
                pet(player);
            }
            return InteractionResult.SUCCESS;
        }
        return super.mobInteract(player, hand);
    }

    public void openPetScreen(ServerPlayer player) {
        player.openMenu(new PetMenu.Provider(this));
        player.level().playSound(null, player.blockPosition(), ModSounds.PAGER_OPEN, SoundSource.PLAYERS, 0.6F, 1.0F);
    }

    private void tameBy(Player player) {
        tame(player);
        this.navigation.stop();
        setTarget(null);
        setMode(Mode.FOLLOW);
        setHealth(getMaxHealth());
        if (!hasCustomName()) {
            List<String> names = this.species.names();
            setCustomName(Component.literal(names.get(this.random.nextInt(names.size()))));
        }
        this.needs.addBond(10);
        syncNeeds();
        playAction(PetAction.TAMED);
        playSound(ModSounds.PET_TAME, 1.0F, 1.0F);
        level().broadcastEntityEvent(this, (byte) 7);
        player.sendSystemMessage(Component.translatable("message.tamagotchi.tamed", getName()).withStyle(ChatFormatting.LIGHT_PURPLE));
        player.sendSystemMessage(Component.translatable("message.tamagotchi.tamed_help").withStyle(ChatFormatting.GRAY));
        if (!player.getInventory().contains(new ItemStack(ModItems.TAMA_PAGER))) {
            ItemStack pager = new ItemStack(ModItems.TAMA_PAGER);
            player.getInventory().placeItemBackInInventory(pager, net.minecraft.util.Prediction.SERVER_ONLY);
            player.sendSystemMessage(Component.translatable("message.tamagotchi.got_pager").withStyle(ChatFormatting.GOLD));
        }
    }

    public void pet(Player player) {
        wakeUp();
        playAction(PetAction.PETTED);
        playSound(ModSounds.PET_PETTING, 0.8F, getVoicePitch());
        this.needs.add(Need.FUN, 4);
        if (this.petCooldown <= 0) {
            this.needs.addBond(1.0F);
            this.petCooldown = 600;
        }
        syncNeeds();
        showNeedsBubble();
    }

    public void groom(Player player) {
        playAction(PetAction.GROOMED);
        playSound(ModSounds.ITEM_BRUSH, 0.8F, 1.0F);
        this.needs.add(Need.HYGIENE, 34);
        this.needs.add(Need.FUN, 2);
        this.needs.addBond(0.5F);
        syncNeeds();
        sparkle(8);
    }

    public void playWith(Player player) {
        playAction(PetAction.PLAY);
        playSound(ModSounds.TOY_SQUEAK, 0.8F, 1.0F + this.random.nextFloat() * 0.2F);
        this.needs.add(Need.FUN, 12);
        this.needs.add(Need.ENERGY, -3);
        this.needs.addBond(0.4F);
        syncNeeds();
    }

    public boolean isPetFood(ItemStack stack) {
        return stack.is(ModItems.PET_KIBBLE) || stack.is(this.species.favoriteTreat()) || this.species.diet().accepts(stack);
    }

    /** Hunger restored by one item. */
    public float foodValue(ItemStack stack) {
        if (stack.is(ModItems.PET_KIBBLE)) return 30;
        if (stack.is(this.species.favoriteTreat())) return 35;
        FoodProperties food = stack.get(DataComponents.FOOD);
        return food != null ? 6 + food.nutrition() * 4 : 18;
    }

    private void feedFrom(Player player, ItemStack stack) {
        boolean favorite = stack.is(this.species.favoriteTreat());
        eat(stack.copyWithCount(1));
        stack.consume(1, player);
        if (favorite) {
            this.needs.addBond(2.0F);
            this.needs.add(Need.FUN, 10);
            player.sendOverlayMessage(Component.translatable("message.tamagotchi.favorite", getName()));
        } else {
            this.needs.addBond(0.4F);
        }
        syncNeeds();
    }

    /** Eats one item (from the player, the bowl or its own backpack). */
    public void eat(ItemStack one) {
        wakeUp();
        this.needs.add(Need.HUNGER, foodValue(one));
        heal(one.is(this.species.favoriteTreat()) ? 8 : 4);
        playAction(PetAction.EAT);
        playSound(ModSounds.PET_EAT, 0.8F, getVoicePitch());
        if (level() instanceof ServerLevel level) {
            level.sendParticles(new net.minecraft.core.particles.ItemParticleOption(ParticleTypes.ITEM, one.getItem()),
                    getX(), getY() + getBbHeight() * 0.5, getZ(), 6, 0.15, 0.1, 0.15, 0.05);
        }
        syncNeeds();
    }

    // ------------------------------------------------------------------ ticking

    @Override
    public void tick() {
        super.tick();
        if (level().isClientSide()) {
            clientTick();
        }
    }

    @Override
    public void aiStep() {
        super.aiStep();
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        if (this.serverActionTicks > 0) {
            this.serverActionTicks--;
        }
        if (this.petCooldown > 0) {
            this.petCooldown--;
        }
        if (this.talentCooldown > 0) {
            this.talentCooldown--;
        }
        for (int i = 0; i < this.beepCooldown.length; i++) {
            if (this.beepCooldown[i] > 0) {
                this.beepCooldown[i]--;
            }
        }
        setFlag(F_AGGRESSIVE, getTarget() != null && getTarget().isAlive());
        if (++this.ticksToNeeds >= 20) {
            this.ticksToNeeds = 0;
            secondTick(level);
        }
        Talents.tick(this, level);
        if (this.species.gait() == PetSpecies.Gait.FLOAT && !onGround() && getDeltaMovement().y < -0.08) {
            setDeltaMovement(getDeltaMovement().multiply(1.0, 0.6, 1.0));   // the wisp glides down
        }
    }

    private void secondTick(ServerLevel level) {
        if (!isTame()) {
            return;
        }
        this.needs.tickSecond(isSleeping(), isInSittingPose());
        // slow regeneration while fed
        if (this.needs.hunger > 40 && getHealth() < getMaxHealth() && this.tickCount % 200 == 0) {
            heal(1.0F);
        }
        syncNeeds();
        if (--this.emoteCooldown <= 0) {
            this.emoteCooldown = 12 + this.random.nextInt(8);
            emoteNeeds(level);
        }
        LivingEntity owner = getOwner();
        if (owner instanceof ServerPlayer player) {
            pagerChecks(player);
            int lvl = player.experienceLevel;
            if (this.lastOwnerLevel >= 0 && lvl > this.lastOwnerLevel && distanceToSqr(player) < 256) {
                playAction(PetAction.CELEBRATE);
                playSound(ModSounds.PET_CELEBRATE, 0.8F, getVoicePitch());
                emote(level, ModParticles.EMOTE_LOVE);
            }
            this.lastOwnerLevel = lvl;
        }
    }

    private void emoteNeeds(ServerLevel level) {
        if (isSleeping()) {
            level.sendParticles(ModParticles.ZZZ, getX(), getY() + getBbHeight() + 0.2, getZ(), 1, 0.1, 0.05, 0.1, 0.0);
            if (this.random.nextInt(3) == 0) {
                playSound(ModSounds.PET_SNORE, 0.4F, getVoicePitch());
            }
            return;
        }
        Need low = this.needs.lowest();
        if (this.needs.get(low) < 30) {
            emote(level, switch (low) {
                case HUNGER -> ModParticles.EMOTE_HUNGRY;
                case FUN -> ModParticles.EMOTE_BORED;
                case ENERGY -> ModParticles.EMOTE_SLEEPY;
                case HYGIENE -> ModParticles.EMOTE_DIRTY;
            });
            if (low == Need.HYGIENE) {
                level.sendParticles(ModParticles.STINK, getX(), getY() + getBbHeight() * 0.7, getZ(), 2, 0.25, 0.2, 0.25, 0.0);
            }
        } else if (this.needs.mood() == Mood.MISERABLE) {
            emote(level, ModParticles.EMOTE_SAD);
        } else if (this.needs.mood() == Mood.ECSTATIC && this.random.nextInt(3) == 0) {
            sparkle(2);
        }
    }

    public void emote(ServerLevel level, ParticleOptions particle) {
        level.sendParticles(particle, getX(), getY() + getBbHeight() + 0.45, getZ(), 1, 0, 0, 0, 0);
    }

    public void sparkle(int count) {
        if (level() instanceof ServerLevel level) {
            level.sendParticles(ModParticles.SPARKLE, getX(), getY() + getBbHeight() * 0.6, getZ(), count, 0.35, 0.3, 0.35, 0.0);
        }
    }

    /** Shown when petted: the most urgent need as a bubble, or a heart when all is well. */
    public void showNeedsBubble() {
        if (!(level() instanceof ServerLevel level)) {
            return;
        }
        Need low = this.needs.lowest();
        if (this.needs.get(low) < 45) {
            emote(level, switch (low) {
                case HUNGER -> ModParticles.EMOTE_HUNGRY;
                case FUN -> ModParticles.EMOTE_BORED;
                case ENERGY -> ModParticles.EMOTE_SLEEPY;
                case HYGIENE -> ModParticles.EMOTE_DIRTY;
            });
        } else {
            emote(level, ModParticles.EMOTE_LOVE);
        }
    }

    /** Pager beeps when a need gets low or the pet is hurt (only if the owner carries a pager). */
    private void pagerChecks(ServerPlayer owner) {
        if (!owner.getInventory().contains(new ItemStack(ModItems.TAMA_PAGER)) || owner.level() != level()) {
            return;
        }
        for (Need need : Need.values()) {
            int i = need.ordinal();
            if (this.needs.get(need) < 22 && this.beepCooldown[i] <= 0) {
                this.beepCooldown[i] = 20 * 120;
                beep(owner, Component.translatable("message.tamagotchi.need." + need.name().toLowerCase(java.util.Locale.ROOT), getName()));
            }
        }
        if (getHealth() < getMaxHealth() * 0.3F && this.beepCooldown[4] <= 0) {
            this.beepCooldown[4] = 20 * 30;
            beep(owner, Component.translatable("message.tamagotchi.need.hurt", getName()));
        }
    }

    private void beep(ServerPlayer owner, Component message) {
        owner.sendOverlayMessage(Component.literal("♪ ").append(message).withStyle(ChatFormatting.LIGHT_PURPLE));
        owner.level().playSound(null, owner.blockPosition(), ModSounds.PAGER_BEEP, SoundSource.PLAYERS, 0.7F, 1.0F);
    }

    public boolean talentReady() {
        return this.talentCooldown <= 0;
    }

    /** Talent cool-downs shrink with bond (up to 40 % shorter at full bond). */
    public void startTalentCooldown(int ticks) {
        this.talentCooldown = Math.round(ticks * (1F - this.needs.bond / 250F));
    }

    public boolean moodAllowsTalent() {
        return !isTame() || this.needs.mood().atLeast(Mood.OKAY);
    }

    private void clientTick() {
        if (this.tickCount >= this.nextBlinkTick) {
            this.blinkUntil = this.tickCount + 3;
            this.nextBlinkTick = this.tickCount + 50 + this.random.nextInt(90);
        }
        if (isSleeping() && this.random.nextInt(50) == 0) {
            level().addParticle(ModParticles.ZZZ, getX(), getY() + getBbHeight(), getZ(), 0, 0.02, 0);
        }
        if (this.species == PetSpecies.VOID_KITTEN && this.random.nextInt(8) == 0) {
            level().addParticle(ParticleTypes.PORTAL, getRandomX(0.5), getRandomY() - 0.2, getRandomZ(0.5),
                    (this.random.nextDouble() - 0.5) * 0.5, -this.random.nextDouble() * 0.3, (this.random.nextDouble() - 0.5) * 0.5);
        }
        if (this.species == PetSpecies.EMBER_PUP && this.random.nextInt(10) == 0) {
            level().addParticle(this.random.nextBoolean() ? ParticleTypes.SMALL_FLAME : ParticleTypes.SMOKE,
                    getRandomX(0.4), getY() + getBbHeight() * 0.8, getRandomZ(0.4), 0, 0.02, 0);
        }
        if (this.species == PetSpecies.SCULK_WISP && this.random.nextInt(12) == 0) {
            level().addParticle(ParticleTypes.SCULK_SOUL, getRandomX(0.4), getY() + 0.1, getRandomZ(0.4), 0, 0.01, 0);
        }
        if (this.species == PetSpecies.TIDE_DRAGON && isInWater() && this.random.nextInt(6) == 0) {
            level().addParticle(ParticleTypes.BUBBLE, getRandomX(0.5), getRandomY(), getRandomZ(0.5), 0, 0.05, 0);
        }
    }

    // ------------------------------------------------------------------ combat

    @Override
    public boolean wantsToAttack(LivingEntity target, LivingEntity owner) {
        if (target instanceof Creeper) {
            return false;
        }
        if (target instanceof TamableAnimal tame && tame.isTame()) {
            return !owner.equals(tame.getOwner());
        }
        if (target instanceof Player p && owner instanceof Player o && !o.canHarmPlayer(p)) {
            return false;
        }
        return true;
    }

    @Override
    public boolean hurtServer(ServerLevel level, DamageSource source, float amount) {
        if (isInvulnerableTo(level, source)) {
            return false;
        }
        Entity attacker = source.getEntity();
        if (isTame() && attacker != null && attacker.equals(getOwner())) {
            // owners can't hurt their own pet - a whack counts as a pat
            if (attacker instanceof Player p) {
                pet(p);
            }
            return false;
        }
        wakeUp();
        setOrderedToSit(false);
        setInSittingPose(false);
        setFlag(F_DANCING | F_BEGGING | F_WARMING, false);
        boolean hurt = super.hurtServer(level, source, amount);
        if (hurt && isTame()) {
            this.needs.add(Need.FUN, -2);
        }
        return hurt;
    }

    @Override
    public void die(DamageSource source) {
        if (isTame() && level() instanceof ServerLevel level) {
            faint(level);
            return;
        }
        super.die(source);
    }

    /** Tamed pets never die: they faint into a Tama Egg that keeps everything. */
    private void faint(ServerLevel level) {
        setHealth(getMaxHealth() * 0.5F);
        setSleeping(false);
        setFlag(F_DANCING | F_SCARED | F_BEGGING | F_WARMING | F_BATHING | F_RUNNING, false);
        setTarget(null);
        clearFire();
        ItemStack egg = TamaEggItem.fromPet(this);
        ItemEntity item = new ItemEntity(level, getX(), getY() + 0.3, getZ(), egg);
        item.setUnlimitedLifetime();
        item.setDefaultPickUpDelay();
        level.addFreshEntity(item);
        level.sendParticles(ParticleTypes.POOF, getX(), getY() + 0.4, getZ(), 12, 0.3, 0.3, 0.3, 0.02);
        level.playSound(null, blockPosition(), ModSounds.PET_FAINT, SoundSource.NEUTRAL, 1.0F, 1.0F);
        if (getOwner() instanceof ServerPlayer owner) {
            BlockPos p = blockPosition();
            owner.sendSystemMessage(Component.translatable("message.tamagotchi.fainted", getName(), p.getX(), p.getY(), p.getZ())
                    .withStyle(ChatFormatting.GOLD));
        }
        discard();
    }

    @Override
    public boolean doHurtTarget(ServerLevel level, Entity target) {
        boolean hit = super.doHurtTarget(level, target);
        if (hit && isTame()) {
            this.needs.add(Need.ENERGY, -1.5F);
            this.needs.add(Need.FUN, 1.0F);
        }
        return hit;
    }

    // ------------------------------------------------------------------ misc vanilla hooks

    @Override
    public boolean isFood(ItemStack stack) {
        return false;     // no breeding: every pet is one of a kind
    }

    @Override
    public @Nullable AgeableMob getBreedOffspring(ServerLevel level, AgeableMob partner) {
        return null;
    }

    @Override
    public boolean removeWhenFarAway(double distSqr) {
        return false;
    }

    @Override
    public boolean canBreatheUnderwater() {
        return this.species.waterBreathing() || this.species.gait() == PetSpecies.Gait.SWIM;
    }

    @Override
    protected void travelInWater(Vec3 input, double baseGravity, boolean isFalling, double oldY) {
        if (this.species.gait() != PetSpecies.Gait.SWIM) {
            super.travelInWater(input, baseGravity, isFalling, oldY);
            return;
        }
        moveRelative(0.1F, input);
        move(net.minecraft.world.entity.MoverType.SELF, getDeltaMovement());
        setDeltaMovement(getDeltaMovement().scale(0.9));
    }

    @Override
    public boolean isPushedByFluid() {
        return this.species.gait() != PetSpecies.Gait.SWIM;
    }

    @Override
    protected boolean canFlyToOwner() {
        return this.species.flying();
    }

    @Override
    public int getMaxHeadXRot() {
        return isInSittingPose() || isSleeping() ? 20 : super.getMaxHeadXRot();
    }

    @Override
    public boolean isPushable() {
        return !isSleeping() && super.isPushable();
    }

    // ------------------------------------------------------------------ sounds

    @Override
    protected @Nullable SoundEvent getAmbientSound() {
        if (isSleeping()) {
            return null;
        }
        if (isTame() && this.needs.mood().atLeast(Mood.HAPPY) && this.random.nextInt(3) == 0) {
            return ModSounds.species(this.species, "happy");
        }
        return ModSounds.species(this.species, "ambient");
    }

    @Override
    protected SoundEvent getHurtSound(DamageSource source) {
        return ModSounds.species(this.species, "hurt");
    }

    @Override
    protected SoundEvent getDeathSound() {
        return ModSounds.species(this.species, "death");
    }

    @Override
    protected float getSoundVolume() {
        return 0.55F;
    }

    @Override
    public int getAmbientSoundInterval() {
        return 240;
    }

    public SoundEvent attackSound() {
        return ModSounds.species(this.species, "attack");
    }

    public @Nullable UUID ownerUuid() {
        return getOwnerReference() == null ? null : getOwnerReference().getUUID();
    }

    public static net.minecraft.resources.Identifier texture(PetSpecies s, String expression) {
        String suffix = expression.equals("normal") ? "" : "_" + expression;
        return Tamagotchi.id("textures/entity/" + s.id() + "/" + s.id() + suffix + ".png");
    }

    public Vec3 headPos() {
        return position().add(getLookAngle().scale(getBbWidth() * 0.6)).add(0, getBbHeight() * 0.75, 0);
    }
}
