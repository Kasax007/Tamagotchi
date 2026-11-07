package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.model.PetModel;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.texture.OverlayTexture;

/** Full-bright layer for lava cracks, sculk spots, glowing eyes and heart eyes. */
@Environment(EnvType.CLIENT)
public class PetGlowLayer extends RenderLayer<TamaPet, PetModel> {
    public PetGlowLayer(RenderLayerParent<TamaPet, PetModel> parent) {
        super(parent);
    }

    @Override
    public void render(PoseStack poseStack, MultiBufferSource buffers, int light, TamaPet pet, float limbSwing, float limbSwingAmount,
                       float partialTick, float ageInTicks, float netHeadYaw, float headPitch) {
        PetRenderState state = getParentModel().state;
        if (state.glowTexture == null || state.isInvisible) {
            return;
        }
        getParentModel().renderToBuffer(poseStack, buffers.getBuffer(RenderType.eyes(state.glowTexture)), light, OverlayTexture.NO_OVERLAY, -1);
    }
}
