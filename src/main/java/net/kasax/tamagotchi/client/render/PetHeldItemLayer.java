package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.model.PetModel;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;

/** Draws a fetched toy in the pet's mouth (or arms), following the head bone. */
@Environment(EnvType.CLIENT)
public class PetHeldItemLayer extends RenderLayer<PetRenderState, PetModel> {
    public PetHeldItemLayer(RenderLayerParent<PetRenderState, PetModel> parent) {
        super(parent);
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, PetRenderState state, float yRot, float xRot) {
        if (state.heldItem.isEmpty()) {
            return;
        }
        PetModel model = getParentModel();
        poseStack.pushPose();
        model.root().translateAndRotate(poseStack);
        ModelPart body = model.root().hasChild("body") ? model.root().getChild("body") : null;
        if (body != null) {
            body.translateAndRotate(poseStack);
        }
        float[] mouth = mouth(state.species);
        boolean headHolds = mouth[3] > 0 && body != null && body.hasChild("head");
        if (headHolds) {
            body.getChild("head").translateAndRotate(poseStack);
        }
        poseStack.translate(mouth[0] / 16F, mouth[1] / 16F, mouth[2] / 16F);
        poseStack.rotateDegrees(Axis.XP, 90);
        poseStack.scale(0.55F, 0.55F, 0.55F);
        state.heldItem.submit(poseStack, collector, light, OverlayTexture.NO_OVERLAY, state.outlineColor);
        poseStack.popPose();
    }

    /** x, y, z in model pixels, and 1 if relative to the head bone (0 = body). */
    private static float[] mouth(PetSpecies s) {
        return switch (s) {
            case DESERT_DRAGON, JUNGLE_DRAGON, TIDE_DRAGON -> new float[]{0, 1.5F, -8.5F, 1};
            case EMBER_PUP -> new float[]{0, 1.0F, -8.5F, 1};
            case VOID_KITTEN -> new float[]{0, 0.8F, -6.5F, 1};
            case FROST_PENGUIN -> new float[]{0, -0.8F, -5.8F, 1};
            case HEX_TOAD -> new float[]{0, 1.0F, -5.5F, 1};
            case SCULK_WISP -> new float[]{0, -2.0F, -4.2F, 0};
            case PEBBLE_GOLEM -> new float[]{0, -2.0F, -4.2F, 0};
            case MIMIC -> new float[]{0, -6.0F, -4.5F, 0};
        };
    }
}
