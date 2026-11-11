package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.kasax.tamacraft.client.model.PetModel;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.pet.TamaPet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.ItemDisplayContext;

/** Draws a fetched toy in the pet's mouth (or arms), following the head bone. */
public class PetHeldItemLayer extends RenderLayer<TamaPet, PetModel> {
    public PetHeldItemLayer(RenderLayerParent<TamaPet, PetModel> parent) {
        super(parent);
    }

    @Override
    public void render(PoseStack poseStack, MultiBufferSource buffers, int light, TamaPet pet, float limbSwing, float limbSwingAmount,
                       float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
        PetRenderState state = getParentModel().state;
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
        poseStack.mulPose(Axis.XP.rotationDegrees(90));
        poseStack.scale(0.55F, 0.55F, 0.55F);
        Minecraft.getInstance().getItemRenderer().renderStatic(pet, state.heldItem, ItemDisplayContext.GROUND, false, poseStack, buffers, pet.level(),
                light, OverlayTexture.NO_OVERLAY, pet.getId());
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
