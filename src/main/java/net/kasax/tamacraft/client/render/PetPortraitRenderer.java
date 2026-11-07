package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamacraft.block.PetPortraitBlock;
import net.kasax.tamacraft.block.PetPortraitBlockEntity;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.pet.TamaPet;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;

/**
 * The painted pet: its model as a shallow relief on the canvas (so it never pokes through the wall), gently
 * breathing, with its name on the brass plate below.
 */
@Environment(EnvType.CLIENT)
public class PetPortraitRenderer implements BlockEntityRenderer<PetPortraitBlockEntity> {
    /** Canvas and plate positions in pixels (see the block model); the picture faces -Z in the local frame. */
    private static final float CANVAS_Z = 14.5F / 16F - 0.5F;
    private static final float PET_FEET_Y = 4.5F / 16F;
    private static final float PET_HEIGHT = 8.5F / 16F;
    private static final float PLATE_Y = 2.5F / 16F;
    private static final float PLATE_Z = 14F / 16F - 0.5F;
    private static final float PLATE_WIDTH = 8.6F / 16F;
    private final PetStatues statues;
    private final Font font;

    public PetPortraitRenderer(BlockEntityRendererProvider.Context ctx) {
        this.statues = new PetStatues(ctx::bakeLayer);
        this.font = ctx.getFont();
    }

    @Override
    public void render(PetPortraitBlockEntity be, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        PetSpecies species = be.species();
        if (species == null) {
            return;
        }
        Direction facing = be.getBlockState().hasProperty(PetPortraitBlock.FACING) ? be.getBlockState().getValue(PetPortraitBlock.FACING) : Direction.NORTH;
        PetRenderState pose = this.statues.newPose(species, be.backpack() ? TamaPet.F_BACKPACK : 0);
        pose.sitting = false;   // standing: a sitting pet drops its tail out of the frame
        pose.ageInTicks = be.getLevel() != null ? (be.getLevel().getGameTime() % 24000) + partialTick : 0;
        FormattedCharSequence name = Component.literal(be.name()).getVisualOrderText();
        float nameWidth = this.font.width(name);

        poseStack.pushPose();
        poseStack.translate(0.5F, 0, 0.5F);
        poseStack.mulPose(Axis.YP.rotationDegrees(180 - facing.toYRot()));

        poseStack.pushPose();
        poseStack.translate(0, PET_FEET_Y, CANVAS_Z - 0.16F);
        poseStack.mulPose(Axis.YP.rotationDegrees(-12));
        float s = PetStatues.scaleFor(species, PET_HEIGHT);
        poseStack.scale(s, s, s * 0.38F);
        this.statues.render(species, pose, poseStack, buffers, light);
        poseStack.popPose();

        if (nameWidth > 0) {
            poseStack.pushPose();
            poseStack.translate(0, PLATE_Y, PLATE_Z - 0.002F);
            poseStack.mulPose(Axis.YP.rotationDegrees(180));
            float ts = Math.min(1F / 130F, PLATE_WIDTH / nameWidth);
            poseStack.scale(ts, -ts, ts);
            this.font.drawInBatch(name, -nameWidth / 2F, -4.5F, 0xFF3B2412, false, poseStack.last().pose(), buffers,
                    Font.DisplayMode.POLYGON_OFFSET, 0, light);
            poseStack.popPose();
        }
        poseStack.popPose();
    }
}
