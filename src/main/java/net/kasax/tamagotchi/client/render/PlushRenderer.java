package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.block.PlushBlock;
import net.kasax.tamagotchi.block.PlushBlockEntity;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.state.properties.RotationSegment;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Draws a plush: the pet's own model, small and sitting, squishing when someone squeezes it. */
@Environment(EnvType.CLIENT)
public class PlushRenderer implements BlockEntityRenderer<PlushBlockEntity, PlushRenderer.State> {
    /** How tall a plush is, in blocks, and how much chubbier than the pet (wider, a bit squat: soft and huggable). */
    public static final float HEIGHT = 0.7F;
    public static final float CHUBBY = 1.12F;
    private final PetStatues statues;
    private final ModelPart tag;

    public static class State extends BlockEntityRenderState {
        PetSpecies species = PetSpecies.DESERT_DRAGON;
        float yaw;
        float squish;
    }

    public PlushRenderer(BlockEntityRendererProvider.Context ctx) {
        this.statues = new PetStatues(ctx::bakeLayer);
        this.tag = ctx.bakeLayer(PlushTag.LAYER);
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(PlushBlockEntity be, State state, float partialTick, Vec3 camera,
                                   ModelFeatureRenderer.@Nullable CrumblingOverlay crumbling) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, camera, crumbling);
        state.species = be.species();
        state.yaw = be.getBlockState().hasProperty(PlushBlock.ROTATION)
                ? RotationSegment.convertToDegrees(be.getBlockState().getValue(PlushBlock.ROTATION)) : 0;
        float t = be.getLevel() == null ? 1 : (be.getLevel().getGameTime() - be.squishedAt + partialTick) / 9F;
        state.squish = t >= 0 && t < 1 ? Mth.sin(t * Mth.PI) : 0;
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.translate(0.5F, 0, 0.5F);
        poseStack.rotateDegrees(Axis.YP, 180 - state.yaw);
        float s = PetStatues.scaleFor(state.species, HEIGHT);
        float wide = CHUBBY * (1 + 0.14F * state.squish);
        poseStack.scale(s * wide, s * 0.95F * (1 - 0.24F * state.squish), s * wide);
        this.statues.submit(state.species, this.statues.pose(state.species), poseStack, collector, state.lightCoords, 0, this.tag);
        poseStack.popPose();
    }
}
