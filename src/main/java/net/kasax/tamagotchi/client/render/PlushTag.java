package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.client.model.PetModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import org.joml.Vector3f;

/** The little heart tag sewn to the side of every plush, so it reads as a cuddly toy and not as a tiny pet. */
@Environment(EnvType.CLIENT)
public final class PlushTag {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Tamagotchi.id("plush_tag"), "main");
    private static final Identifier TEXTURE = Tamagotchi.id("textures/entity/plush_tag.png");

    private PlushTag() {
    }

    /** A flat 7 x 7 px card in the YZ plane (both faces textured), sewn on at its top corner. */
    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        mesh.getRoot().addOrReplaceChild("tag", CubeListBuilder.create().texOffs(0, 0).addBox(0, 0, 0, 0, 7, 7), PartPose.ZERO);
        return LayerDefinition.create(mesh, 16, 16);
    }

    /**
     * Where the tag hangs, in entity-model space (y down): on the pet's left side, a bit below the top of its body and
     * towards the front. Taken from the posed body part, so it fits every pet.
     */
    public static Vector3f anchor(PetModel model, PetRenderState pose) {
        model.setupAnim(pose);
        float[] box = {Float.MAX_VALUE, -Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE, Float.MAX_VALUE, -Float.MAX_VALUE};
        boolean[] found = {false};
        model.root().visit(new PoseStack(), (p, path, i, cube) -> {
            if (!path.equals("/body")) {
                return;
            }
            found[0] = true;
            for (ModelPart.Polygon polygon : cube.polygons) {
                for (ModelPart.Vertex v : polygon.vertices()) {
                    Vector3f w = p.pose().transformPosition(v.worldX(), v.worldY(), v.worldZ(), new Vector3f());
                    box[0] = Math.min(box[0], w.x);
                    box[1] = Math.max(box[1], w.x);
                    box[2] = Math.min(box[2], w.y);
                    box[3] = Math.max(box[3], w.y);
                    box[4] = Math.min(box[4], w.z);
                    box[5] = Math.max(box[5], w.z);
                }
            }
        });
        if (!found[0]) {
            return new Vector3f(0.2F, 1.1F, 0);
        }
        return new Vector3f(box[1], box[2] + (box[3] - box[2]) * 0.3F, box[4] + (box[5] - box[4]) * 0.35F);
    }

    /** Draws the tag at {@code at} (entity-model space, inside the usual entity flip). */
    public static void submit(ModelPart tag, Vector3f at, PoseStack poseStack, SubmitNodeCollector collector, int light, int outline) {
        poseStack.pushPose();
        poseStack.translate(at.x + 0.005F, at.y, at.z);
        poseStack.rotateDegrees(Axis.YP, 62);    // turned towards the front so you see the heart
        poseStack.rotateDegrees(Axis.XP, -8);    // and hanging a little askew
        poseStack.scale(0.65F, 0.65F, 0.65F);
        collector.submitModelPart(tag, poseStack, RenderTypes.entityCutout(TEXTURE), light, OverlayTexture.NO_OVERLAY, null, -1, outline);
        poseStack.popPose();
    }
}
