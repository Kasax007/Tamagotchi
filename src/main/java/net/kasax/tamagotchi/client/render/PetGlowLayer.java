package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.model.PetModel;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;

/** Full-bright layer for lava cracks, sculk spots, glowing eyes and heart eyes. */
@Environment(EnvType.CLIENT)
public class PetGlowLayer extends RenderLayer<PetRenderState, PetModel> {
    public PetGlowLayer(RenderLayerParent<PetRenderState, PetModel> parent) {
        super(parent);
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int light, PetRenderState state, float yRot, float xRot) {
        if (state.glowTexture == null || state.isInvisible) {
            return;
        }
        collector.order(1).submitModel(getParentModel(), state, poseStack, RenderTypes.eyes(state.glowTexture), light,
                OverlayTexture.NO_OVERLAY, state.outlineColor);
    }
}
