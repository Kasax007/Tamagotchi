package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.RunningWheelBlock;
import net.kasax.tamagotchi.block.RunningWheelBlockEntity;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** Draws the spinning wheel of the running wheel; speeds up while a pet runs and coasts to a stop. */
@Environment(EnvType.CLIENT)
public class RunningWheelRenderer implements BlockEntityRenderer<RunningWheelBlockEntity, RunningWheelRenderer.State> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Tamagotchi.id("running_wheel"), "main");
    private static final Identifier TEXTURE = Tamagotchi.id("textures/entity/running_wheel.png");
    private final ModelPart wheel;

    public static class State extends BlockEntityRenderState {
        float angle;
        Direction facing = Direction.NORTH;
    }

    public RunningWheelRenderer(BlockEntityRendererProvider.Context ctx) {
        this.wheel = ctx.bakeLayer(LAYER);
    }

    /** A 14 px wheel: twelve rim slats around the X axis, four spokes and a hub. */
    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        for (int i = 0; i < 12; i++) {
            float a = i * Mth.TWO_PI / 12F;
            root.addOrReplaceChild("slat" + i, CubeListBuilder.create().texOffs(0, 0).addBox(-5, 6, -2, 10, 1, 4),
                    PartPose.offsetAndRotation(0, 0, 0, a, 0, 0));
        }
        for (int i = 0; i < 4; i++) {
            float a = i * Mth.PI / 4F;
            root.addOrReplaceChild("spoke" + i, CubeListBuilder.create().texOffs(0, 6).addBox(-0.5F, -6, -0.5F, 1, 12, 1),
                    PartPose.offsetAndRotation(-4.6F, 0, 0, a, 0, 0));
            root.addOrReplaceChild("spoke_b" + i, CubeListBuilder.create().texOffs(0, 6).addBox(-0.5F, -6, -0.5F, 1, 12, 1),
                    PartPose.offsetAndRotation(4.6F, 0, 0, a, 0, 0));
        }
        root.addOrReplaceChild("hub", CubeListBuilder.create().texOffs(8, 6).addBox(-6, -1, -1, 12, 2, 2), PartPose.ZERO);
        return LayerDefinition.create(mesh, 32, 16);
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(RunningWheelBlockEntity be, State state, float partialTick, Vec3 camera,
                                   ModelFeatureRenderer.@Nullable CrumblingOverlay crumbling) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, camera, crumbling);
        boolean running = be.getBlockState().hasProperty(RunningWheelBlock.RUNNING) && be.getBlockState().getValue(RunningWheelBlock.RUNNING);
        long now = be.getLevel() != null ? be.getLevel().getGameTime() : 0;
        if (be.lastFrameTick != now) {
            float target = running ? 0.32F : 0F;
            be.speed += (target - be.speed) * (running ? 0.12F : 0.04F);
            be.angle += be.speed;
            be.lastFrameTick = now;
        }
        state.angle = be.angle + be.speed * partialTick;
        state.facing = be.getBlockState().hasProperty(RunningWheelBlock.FACING) ? be.getBlockState().getValue(RunningWheelBlock.FACING) : Direction.NORTH;
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        poseStack.pushPose();
        poseStack.translate(0.5F, 0.5F, 0.5F);
        poseStack.rotateDegrees(Axis.YP, 180 - state.facing.toYRot());
        poseStack.rotate(Axis.XP, state.angle);
        collector.submitModelPart(this.wheel, poseStack, RenderTypes.entityCutout(TEXTURE), state.lightCoords, OverlayTexture.NO_OVERLAY, null);
        poseStack.popPose();
    }
}
