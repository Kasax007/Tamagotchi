package net.kasax.tamagotchi.block;

import net.kasax.tamagotchi.registry.ModBlocks;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.Container;
import net.minecraft.world.entity.ContainerUser;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.DispenserMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.ContainerOpenersCounter;
import net.minecraft.world.level.block.entity.DispenserBlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Nine slots of toys. The lid is open while a player looks inside or a pet plays with it. */
public class ToyBoxBlockEntity extends DispenserBlockEntity {
    private static final Component NAME = Component.translatable("block.tamagotchi.toy_box");
    private long petPlayUntil;
    private final ContainerOpenersCounter openers = new ContainerOpenersCounter() {
        @Override
        protected void onOpen(Level level, BlockPos pos, BlockState state) {
            updateLid();
        }

        @Override
        protected void onClose(Level level, BlockPos pos, BlockState state) {
            updateLid();
        }

        @Override
        protected void openerCountChanged(Level level, BlockPos pos, BlockState state, int previous, int current) {
        }

        @Override
        public boolean isOwnContainer(Player player) {
            return player.containerMenu instanceof Menu m && m.box == ToyBoxBlockEntity.this;
        }
    };

    /** The vanilla 3x3 menu, remembering which box it belongs to. */
    static final class Menu extends DispenserMenu {
        final Container box;

        Menu(int id, Inventory inventory, Container box) {
            super(id, inventory, box);
            this.box = box;
        }
    }

    public ToyBoxBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.TOY_BOX_BE, pos, state);
    }

    @Override
    protected Component getDefaultName() {
        return NAME;
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return new Menu(containerId, inventory, this);
    }

    @Override
    public void startOpen(ContainerUser user) {
        if (!this.remove && !user.getLivingEntity().isSpectator()) {
            this.openers.incrementOpeners(user.getLivingEntity(), getLevel(), getBlockPos(), getBlockState(), user.getContainerInteractionRange());
        }
    }

    @Override
    public void stopOpen(ContainerUser user) {
        if (!this.remove && !user.getLivingEntity().isSpectator()) {
            this.openers.decrementOpeners(user.getLivingEntity(), getLevel(), getBlockPos(), getBlockState());
        }
    }

    public void recheckOpen() {
        if (!this.remove) {
            this.openers.recheckOpeners(getLevel(), getBlockPos(), getBlockState());
            updateLid();
        }
    }

    /** A pet plays with the box for {@code ticks}: the lid opens and closes again afterwards. */
    public void petPlay(int ticks) {
        this.petPlayUntil = this.level.getGameTime() + ticks;
        updateLid();
        this.level.scheduleTick(this.worldPosition, getBlockState().getBlock(), ticks + 1);
    }

    private void updateLid() {
        if (this.level == null || this.remove) {
            return;
        }
        BlockState st = getBlockState();
        boolean open = this.openers.getOpenerCount() > 0 || this.level.getGameTime() < this.petPlayUntil;
        if (st.hasProperty(ToyBoxBlock.OPEN) && st.getValue(ToyBoxBlock.OPEN) != open) {
            this.level.setBlock(this.worldPosition, st.setValue(ToyBoxBlock.OPEN, open), Block.UPDATE_ALL);
            this.level.playSound(null, this.worldPosition, open ? SoundEvents.BARREL_OPEN : SoundEvents.BARREL_CLOSE,
                    SoundSource.BLOCKS, 0.5F, open ? 1.3F : 1.2F);
        }
    }

    /** A toy from the box for a pet to show off, preferring real pet toys; empty when the box is empty. */
    public ItemStack pickToy(net.minecraft.util.RandomSource random) {
        ItemStack any = ItemStack.EMPTY;
        int seen = 0;
        for (int i = 0; i < getContainerSize(); i++) {
            ItemStack s = getItem(i);
            if (s.isEmpty()) {
                continue;
            }
            if (isPetToy(s) && random.nextInt(++seen) == 0) {
                any = s;
            } else if (any.isEmpty()) {
                any = s;
            }
        }
        return any;
    }

    public static boolean isPetToy(ItemStack s) {
        return s.is(ModItems.SQUEAKY_BALL) || s.is(ModItems.FEATHER_WAND) || s.is(ModItems.LASER_POINTER)
                || s.getItem() instanceof net.minecraft.world.item.BlockItem b && b.getBlock() instanceof PlushBlock;
    }
}
