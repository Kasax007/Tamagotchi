package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.block.PetPortraitBlock;
import net.kasax.tamagotchi.block.PetPortraitBlockEntity;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.gui.Font;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * The painted pet: its model as a shallow relief on the canvas (so it never pokes through the wall), gently
 * breathing, with its name on the brass plate below.
 */
@Environment(EnvType.CLIENT)
public class PetPortraitRenderer implements BlockEntityRenderer<PetPortraitBlockEntity, PetPortraitRenderer.State> {
    /** Canvas and plate positions in pixels (see the block model); the picture faces -Z in the local frame. */
    private static final float CANVAS_Z = 14.5F / 16F - 0.5F;
    private static final float PET_FEET_Y = 4.5F / 16F;
    private static final float PET_HEIGHT = 8.5F / 16F;
    private static final float PLATE_Y = 2.5F / 16F;
    private static final float PLATE_Z = 14F / 16F - 0.5F;
    private static final float PLATE_WIDTH = 8.6F / 16F;
    private final PetStatues statues;
    private final Font font;

    public static class State extends BlockEntityRenderState {
        Direction facing = Direction.NORTH;
        @Nullable PetSpecies species;
        @Nullable FormattedCharSequence name;
        float nameWidth;
        @Nullable PetRenderState pose;
    }

    public PetPortraitRenderer(BlockEntityRendererProvider.Context ctx) {
        this.statues = new PetStatues(ctx::bakeLayer);
        this.font = ctx.font();
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(PetPortraitBlockEntity be, State state, float partialTick, Vec3 camera,
                                   ModelFeatureRenderer.@Nullable CrumblingOverlay crumbling) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, camera, crumbling);
        state.facing = be.getBlockState().hasProperty(PetPortraitBlock.FACING) ? be.getBlockState().getValue(PetPortraitBlock.FACING) : Direction.NORTH;
        state.species = be.species();
        if (state.species == null) {
            state.pose = null;
            state.name = null;
            return;
        }
        PetRenderState pose = this.statues.newPose(state.species, be.backpack() ? TamaPet.F_BACKPACK : 0);
        pose.sitting = false;   // standing: a sitting pet drops its tail out of the frame
        pose.ageInTicks = be.getLevel() != null ? (be.getLevel().getGameTime() % 24000) + partialTick : 0;
        state.pose = pose;
        state.name = Component.literal(be.name()).getVisualOrderText();
        state.nameWidth = this.font.width(state.name);
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (state.species == null || state.pose == null) {
            return;
        }
        poseStack.pushPose();
        poseStack.translate(0.5F, 0, 0.5F);
        poseStack.rotateDegrees(Axis.YP, 180 - state.facing.toYRot());

        poseStack.pushPose();
        poseStack.translate(0, PET_FEET_Y, CANVAS_Z - 0.16F);
        poseStack.rotateDegrees(Axis.YP, -12);
        float s = PetStatues.scaleFor(state.species, PET_HEIGHT);
        poseStack.scale(s, s, s * 0.38F);
        this.statues.submit(state.species, state.pose, poseStack, collector, state.lightCoords, 0);
        poseStack.popPose();

        if (state.name != null && state.nameWidth > 0) {
            poseStack.pushPose();
            poseStack.translate(0, PLATE_Y, PLATE_Z - 0.002F);
            poseStack.rotateDegrees(Axis.YP, 180);
            float ts = Math.min(1F / 130F, PLATE_WIDTH / state.nameWidth);
            poseStack.scale(ts, -ts, ts);
            collector.submitText(poseStack, -state.nameWidth / 2F, -4.5F, state.name, false, Font.DisplayMode.POLYGON_OFFSET,
                    state.lightCoords, 0xFF3B2412, 0, 0);
            poseStack.popPose();
        }
        poseStack.popPose();
    }
}
