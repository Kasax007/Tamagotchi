package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import java.util.EnumMap;
import java.util.Map;
import java.util.function.Function;
import net.kasax.tamacraft.client.TamacraftClient;
import net.kasax.tamacraft.client.model.PetModel;
import net.kasax.tamacraft.pet.PetSpecies;
import net.kasax.tamacraft.pet.TamaPet;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.texture.OverlayTexture;
import org.joml.Vector3f;
import org.jetbrains.annotations.Nullable;

/**
 * The pets' own models, posed sitting and smiling, for plushies, portraits and their items. One model and one pose
 * per kind; {@link #submit} draws one with its feet on the current origin, facing -Z.
 */
public final class PetStatues {
    private final Map<PetSpecies, PetModel> models = new EnumMap<>(PetSpecies.class);
    private final Map<PetSpecies, PetRenderState> poses = new EnumMap<>(PetSpecies.class);
    private final Map<PetSpecies, Vector3f> tagAnchors = new EnumMap<>(PetSpecies.class);

    public PetStatues(Function<ModelLayerLocation, ModelPart> baker) {
        for (PetSpecies s : PetSpecies.values()) {
            this.models.put(s, new PetModel(baker.apply(TamacraftClient.LAYERS.get(s)), s));
            this.poses.put(s, pose(s, 0));
        }
    }

    private static PetRenderState pose(PetSpecies s, int flags) {
        PetRenderState st = new PetRenderState();
        st.species = s;
        st.sitting = true;
        st.tame = true;
        st.mood = 95;
        st.flags = flags;
        st.expression = "happy";
        st.texture = TamaPet.texture(s, "happy");
        return st;
    }

    public PetModel model(PetSpecies s) {
        return this.models.get(s);
    }

    public PetRenderState pose(PetSpecies s) {
        return this.poses.get(s);
    }

    /** A separate pose (e.g. with the backpack on, or breathing) that the caller may change. */
    public PetRenderState newPose(PetSpecies s, int flags) {
        return pose(s, flags);
    }

    /** Scale that makes the pet about {@code height} blocks tall. */
    public static float scaleFor(PetSpecies s, float height) {
        return height * PetRenderer.MODEL_SCALE / s.height();
    }

    /** Draws the pet (entity-model space: y down, 24 px = the ground) on the origin, facing -Z. */
    public void render(PetSpecies s, PetRenderState pose, PoseStack poseStack, MultiBufferSource buffers, int light) {
        render(s, pose, poseStack, buffers, light, null);
    }

    /** The same, with a plush heart tag sewn on. */
    public void render(PetSpecies s, PetRenderState pose, PoseStack poseStack, MultiBufferSource buffers, int light, @Nullable ModelPart tag) {
        poseStack.pushPose();
        poseStack.scale(-1, -1, 1);
        poseStack.translate(0, -1.501F, 0);
        PetModel model = this.models.get(s);
        Vector3f anchor = tag == null ? null : this.tagAnchors.computeIfAbsent(s, k -> PlushTag.anchor(model, this.poses.get(k)));
        model.pose(pose);
        model.renderToBuffer(poseStack, buffers.getBuffer(model.renderType(pose.texture)), light, OverlayTexture.NO_OVERLAY, -1);
        if (tag != null) {
            PlushTag.render(tag, anchor, poseStack, buffers, light);
        }
        poseStack.popPose();
    }
}
