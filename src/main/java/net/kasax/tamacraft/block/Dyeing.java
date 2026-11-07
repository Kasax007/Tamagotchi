package net.kasax.tamacraft.block;

import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.FastColor;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.DyeItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.EnumProperty;

/** Dyeable pet furniture: right-click it with any dye to recolour the fabric. */
public final class Dyeing {
    public static final EnumProperty<DyeColor> COLOR = EnumProperty.create("color", DyeColor.class);
    public static final EnumProperty<DyeColor> BACKDROP = EnumProperty.create("backdrop", DyeColor.class);

    private Dyeing() {
    }

    /** Recolours {@code prop} with the dye in {@code stack}; anything else falls through to the empty-hand use. */
    public static ItemInteractionResult apply(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player,
                                          EnumProperty<DyeColor> prop) {
        DyeColor dye = stack.getItem() instanceof DyeItem d ? d.getDyeColor() : null;
        if (dye == null) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (state.getValue(prop) == dye) {
            return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
        }
        if (!level.isClientSide()) {
            level.setBlockAndUpdate(pos, state.setValue(prop, dye));
            stack.consume(1, player);
            level.playSound(null, pos, SoundEvents.DYE_USE, SoundSource.BLOCKS, 1.0F, 1.0F);
        }
        return ItemInteractionResult.sidedSuccess(level.isClientSide());
    }

    /** How much white goes into the dye colour: none for fabric, some for the glowing lamp shell, lots for the backdrop. */
    public static final float FABRIC = 0F;
    public static final float LAMP = 0.3F;
    public static final float PASTEL = 0.55F;

    /** The tint of a dyed part (opaque ARGB); the item models use the same values for their default colours. */
    public static int tint(DyeColor c, float whiten) {
        return FastColor.ARGB32.opaque(FastColor.ARGB32.lerp(whiten, c.getTextureDiffuseColor(), 0xFFFFFFFF));
    }
}
