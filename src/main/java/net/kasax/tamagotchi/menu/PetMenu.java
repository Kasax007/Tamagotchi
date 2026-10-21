package net.kasax.tamagotchi.menu;

import net.fabricmc.fabric.api.menu.v1.ExtendedMenuProvider;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModMenus;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.jspecify.annotations.Nullable;

/**
 * The pet screen opened with the Tama Pager: the pet's belly/backpack slots plus the player
 * inventory; Sit / Follow / Wander go through {@link #clickMenuButton}.
 */
public class PetMenu extends AbstractContainerMenu {
    /** Width of the info panel left of the slots, shared with the screen. */
    public static final int INFO_W = 124;
    public static final int SLOT_X = INFO_W + 8;
    public static final int SLOT_Y = 18;

    public record Data(int entityId, int slots) {
        public static final StreamCodec<RegistryFriendlyByteBuf, Data> CODEC = StreamCodec.composite(
                ByteBufCodecs.VAR_INT, Data::entityId, ByteBufCodecs.VAR_INT, Data::slots, Data::new);
    }

    private final @Nullable TamaPet pet;
    private final Container storage;
    private final int storageSlots;

    public PetMenu(int id, Inventory inventory, Data data) {
        this(id, inventory, inventory.player.level().getEntity(data.entityId()) instanceof TamaPet p ? p : null, data.slots(),
                new SimpleContainer(TamaPet.BACKPACK_SLOTS * 2));
    }

    public PetMenu(int id, Inventory inventory, @Nullable TamaPet pet, int slots, Container storage) {
        super(ModMenus.PET_MENU, id);
        this.pet = pet;
        this.storage = storage;
        this.storageSlots = slots;
        storage.startOpen(inventory.player);
        for (int i = 0; i < slots; i++) {
            addSlot(new Slot(storage, i, SLOT_X + (i % 9) * 18, SLOT_Y + (i / 9) * 18));
        }
        int invY = SLOT_Y + rowsShown(slots) * 18 + 14;
        for (int r = 0; r < 3; r++) {
            for (int c = 0; c < 9; c++) {
                addSlot(new Slot(inventory, c + r * 9 + 9, SLOT_X + c * 18, invY + r * 18));
            }
        }
        for (int c = 0; c < 9; c++) {
            addSlot(new Slot(inventory, c, SLOT_X + c * 18, invY + 58));
        }
    }

    public static int rowsShown(int slots) {
        return Math.max(3, slots / 9);
    }

    public @Nullable TamaPet pet() {
        return this.pet;
    }

    public int storageSlots() {
        return this.storageSlots;
    }

    @Override
    public boolean clickMenuButton(Player player, int id) {
        if (this.pet == null || !this.pet.isOwnedBy(player)) {
            return false;
        }
        switch (id) {
            case 0 -> this.pet.setMode(TamaPet.Mode.SIT);
            case 1 -> this.pet.setMode(TamaPet.Mode.FOLLOW);
            case 2 -> this.pet.setMode(TamaPet.Mode.WANDER);
            default -> {
                return false;
            }
        }
        return true;
    }

    @Override
    public ItemStack quickMoveStack(Player player, int index) {
        ItemStack copy = ItemStack.EMPTY;
        Slot slot = this.slots.get(index);
        if (slot.hasItem()) {
            ItemStack stack = slot.getItem();
            copy = stack.copy();
            if (index < this.storageSlots) {
                if (!moveItemStackTo(stack, this.storageSlots, this.slots.size(), true)) {
                    return ItemStack.EMPTY;
                }
            } else if (this.storageSlots == 0 || !moveItemStackTo(stack, 0, this.storageSlots, false)) {
                return ItemStack.EMPTY;
            }
            if (stack.isEmpty()) {
                slot.setByPlayer(ItemStack.EMPTY);
            } else {
                slot.setChanged();
            }
        }
        return copy;
    }

    @Override
    public boolean stillValid(Player player) {
        return this.pet != null && this.pet.isAlive() && this.pet.isOwnedBy(player) && this.pet.level() == player.level()
                && this.pet.distanceToSqr(player) < 72 * 72 && this.pet.storageSlots() == this.storageSlots;
    }

    @Override
    public void removed(Player player) {
        super.removed(player);
        this.storage.stopOpen(player);
    }

    /** Opens the menu for a pet; the client learns which entity and how many slots. */
    public record Provider(TamaPet pet) implements ExtendedMenuProvider<Data> {
        @Override
        public Data getScreenOpeningData(ServerPlayer player) {
            return new Data(this.pet.getId(), this.pet.storageSlots());
        }

        @Override
        public Component getDisplayName() {
            return this.pet.getName();
        }

        @Override
        public AbstractContainerMenu createMenu(int id, Inventory inventory, Player player) {
            return new PetMenu(id, inventory, this.pet, this.pet.storageSlots(), this.pet.inventory());
        }
    }
}
