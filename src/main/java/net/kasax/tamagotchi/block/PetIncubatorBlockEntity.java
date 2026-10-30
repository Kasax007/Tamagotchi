package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.item.TamaEggItem;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.TagValueOutput;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Holds one egg and the game time it hatches at; the client draws the egg wobbling harder as that time comes. */
public class PetIncubatorBlockEntity extends BlockEntity {
    public static final int HATCH_TICKS = 600;
    private ItemStack egg = ItemStack.EMPTY;
    private long hatchAt;

    public PetIncubatorBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.PET_INCUBATOR_BE, pos, state);
    }

    public ItemStack getEgg() {
        return this.egg;
    }

    /** 0 when the egg just went in, 1 when it hatches. */
    public float progress(float partialTick) {
        if (this.egg.isEmpty() || this.level == null) {
            return 0;
        }
        float left = this.hatchAt - this.level.getGameTime() - partialTick;
        return Math.clamp(1F - left / HATCH_TICKS, 0F, 1F);
    }

    public void insert(ItemStack one, @Nullable Player player) {
        this.egg = one;
        this.hatchAt = this.level.getGameTime() + HATCH_TICKS;
        this.level.playSound(null, this.worldPosition, SoundEvents.SNIFFER_EGG_PLOP, SoundSource.BLOCKS, 0.8F, 1.3F);
        if (player != null && TamaEggItem.species(one) != null) {
            player.sendOverlayMessage(Component.translatable("message.tamagotchi.incubating", one.getHoverName()));
        }
        changed(true);
    }

    public ItemStack takeEgg() {
        ItemStack out = this.egg;
        this.egg = ItemStack.EMPTY;
        changed(false);
        return out;
    }

    private void changed(boolean lit) {
        setChanged();
        BlockState st = getBlockState();
        if (st.getValue(PetIncubatorBlock.LIT) != lit) {
            this.level.setBlock(this.worldPosition, st.setValue(PetIncubatorBlock.LIT, lit), Block.UPDATE_ALL);
        } else {
            this.level.sendBlockUpdated(this.worldPosition, st, st, Block.UPDATE_ALL);
        }
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, PetIncubatorBlockEntity be) {
        if (be.egg.isEmpty() || !(level instanceof ServerLevel server)) {
            return;
        }
        long left = be.hatchAt - level.getGameTime();
        if (left > HATCH_TICKS) {   // the clock went back (e.g. /time set): restart
            be.hatchAt = level.getGameTime() + HATCH_TICKS;
            be.setChanged();
        }
        Vec3 c = Vec3.atBottomCenterOf(pos);
        if (left % 40 == 0) {
            server.sendParticles(ParticleTypes.HAPPY_VILLAGER, c.x, c.y + 0.6, c.z, 1, 0.2, 0.1, 0.2, 0);
        }
        if (left == 100 || left == 50 || left == 20) {
            server.playSound(null, pos, SoundEvents.SNIFFER_EGG_CRACK, SoundSource.BLOCKS, 0.7F, 1.4F);
        }
        if (left > 0) {
            return;
        }
        if (TamaEggItem.species(be.egg) == null) {
            Containers.dropItemStack(level, c.x, c.y + 0.8, c.z, be.takeEgg());   // a blank egg: nothing to hatch
            return;
        }
        Direction front = state.getValue(PetIncubatorBlock.FACING);
        BlockPos out = pos.relative(front);
        Vec3 at = server.getBlockState(out).getCollisionShape(server, out).isEmpty() ? Vec3.atBottomCenterOf(out) : c.add(0, 0.8, 0);
        TamaPet pet = TamaEggItem.wake(server, be.egg, at, front.toYRot(), true);
        if (pet != null) {
            server.playSound(null, pos, SoundEvents.SNIFFER_EGG_HATCH, SoundSource.BLOCKS, 0.9F, 1.3F);
            server.sendParticles(ParticleTypes.HAPPY_VILLAGER, c.x, c.y + 0.6, c.z, 12, 0.3, 0.3, 0.3, 0);
            be.egg = ItemStack.EMPTY;
            be.changed(false);
        }
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        this.egg = input.read("egg", ItemStack.CODEC).orElse(ItemStack.EMPTY);
        this.hatchAt = input.getLongOr("hatch_at", 0L);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (!this.egg.isEmpty()) {
            output.store("egg", ItemStack.CODEC, this.egg);
        }
        output.putLong("hatch_at", this.hatchAt);
    }

    @Override
    public ClientboundBlockEntityDataPacket getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        TagValueOutput out = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, registries);
        saveAdditional(out);
        return out.buildResult();
    }

    @Override
    public void preRemoveSideEffects(BlockPos pos, BlockState state) {
        if (this.level != null && !this.egg.isEmpty()) {
            Containers.dropItemStack(this.level, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, this.egg);
            this.egg = ItemStack.EMPTY;
        }
    }
}
