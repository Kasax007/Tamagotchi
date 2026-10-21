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

    /** Axle height in pixels (matches the stand in the block model). */
    public static final float HUB_Y = 12F;

    /**
     * A big hamster wheel (radius 11 px) around the local Z axis, which points to the open front: eighteen rim
     * slats, eight spokes on the back only so you can see the pet inside, and a short axle into the stand.
     */
    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        for (int i = 0; i < 18; i++) {
            float a = i * Mth.TWO_PI / 18F;
            root.addOrReplaceChild("slat" + i, CubeListBuilder.create().texOffs(0, 0).addBox(-1.5F, 10, -6, 3, 1, 12),
                    PartPose.offsetAndRotation(0, 0, 0, 0, 0, a));
        }
        for (int i = 0; i < 8; i++) {
            float a = i * Mth.TWO_PI / 8F;
            root.addOrReplaceChild("spoke" + i, CubeListBuilder.create().texOffs(32, 0).addBox(-0.5F, 0, -0.5F, 1, 10, 1),
                    PartPose.offsetAndRotation(0, 0, -5.5F, 0, 0, a));
        }
        root.addOrReplaceChild("hub", CubeListBuilder.create().texOffs(40, 0).addBox(-1.5F, -1.5F, -7, 3, 3, 2), PartPose.ZERO);
        return LayerDefinition.create(mesh, 64, 32);
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
        poseStack.translate(0.5F, HUB_Y / 16F, 0.5F);
        poseStack.rotateDegrees(Axis.YP, -state.facing.toYRot());   // local +Z = the open front
        poseStack.rotate(Axis.ZP, state.angle);
        collector.submitModelPart(this.wheel, poseStack, RenderTypes.entityCutout(TEXTURE), state.lightCoords, OverlayTexture.NO_OVERLAY, null);
        poseStack.popPose();
    }
}
