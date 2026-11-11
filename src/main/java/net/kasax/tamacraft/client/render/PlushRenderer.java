package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.kasax.tamacraft.block.PlushBlock;
import net.kasax.tamacraft.block.PlushBlockEntity;
import net.kasax.tamacraft.pet.PetSpecies;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.state.properties.RotationSegment;

/** Draws a plush: the pet's own model, small and sitting, squishing when someone squeezes it. */
public class PlushRenderer implements BlockEntityRenderer<PlushBlockEntity> {
    /** How tall a plush is, in blocks, and how much chubbier than the pet (wider, a bit squat: soft and huggable). */
    public static final float HEIGHT = 0.7F;
    public static final float CHUBBY = 1.12F;
    private final PetStatues statues;
    private final ModelPart tag;

    public PlushRenderer(BlockEntityRendererProvider.Context ctx) {
        this.statues = new PetStatues(ctx::bakeLayer);
        this.tag = ctx.bakeLayer(PlushTag.LAYER);
    }

    @Override
    public void render(PlushBlockEntity be, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        PetSpecies species = be.species();
        float yaw = be.getBlockState().hasProperty(PlushBlock.ROTATION)
                ? RotationSegment.convertToDegrees(be.getBlockState().getValue(PlushBlock.ROTATION)) : 0;
        float t = be.getLevel() == null ? 1 : (be.getLevel().getGameTime() - be.squishedAt + partialTick) / 9F;
        float squish = t >= 0 && t < 1 ? Mth.sin(t * Mth.PI) : 0;
        poseStack.pushPose();
        poseStack.translate(0.5F, 0, 0.5F);
        poseStack.mulPose(Axis.YP.rotationDegrees(180 - yaw));
        float s = PetStatues.scaleFor(species, HEIGHT);
        float wide = CHUBBY * (1 + 0.14F * squish);
        poseStack.scale(s * wide, s * 0.95F * (1 - 0.24F * squish), s * wide);
        this.statues.render(species, this.statues.pose(species), poseStack, buffers, light, this.tag);
        poseStack.popPose();
    }
}
