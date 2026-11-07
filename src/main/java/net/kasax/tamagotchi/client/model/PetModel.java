package net.kasax.tamagotchi.client.model;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.render.PetRenderState;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.RenderType;
import org.jetbrains.annotations.Nullable;

/**
 * One model class for every pet. The geometry comes from the generated {@link PetModels}
 * layers; all motion is done by {@link PetAnimator}, which works on bone names, so any pet that
 * has e.g. a "tail" bone gets tail animations for free.
 *
 * <p>The pose comes from a {@link PetRenderState}: {@link PetRenderer} fills {@link #state} before vanilla calls
 * {@link #setupAnim}; plushies and portraits pose the model with {@link #pose} directly.
 */
@Environment(EnvType.CLIENT)
public class PetModel extends EntityModel<TamaPet> {
    final PetSpecies species;
    private final ModelPart root;
    /** The state of the pet being drawn right now (filled by the renderer). */
    public PetRenderState state = new PetRenderState();
    final @Nullable ModelPart body, head, jaw, earL, earR, tail, tail2, tail3, wingL, wingR;
    final @Nullable ModelPart legFL, legFR, legBL, legBR, legL, legR, armL, armR;
    final @Nullable ModelPart backpack, tongue, scarfTail, antennaL, antennaR, sproutL, sproutR, hat, hatTip, crest, flower;

    public PetModel(ModelPart root, PetSpecies species) {
        super(RenderType::entityCutoutNoCull);
        this.root = root;
        this.species = species;
        this.body = find(root, "body");
        this.head = find(root, "head");
        this.jaw = find(root, "jaw");
        this.earL = find(root, "ear_l");
        this.earR = find(root, "ear_r");
        this.tail = find(root, "tail");
        this.tail2 = find(root, "tail2");
        this.tail3 = find(root, "tail3");
        this.wingL = find(root, "wing_l");
        this.wingR = find(root, "wing_r");
        this.legFL = find(root, "leg_fl");
        this.legFR = find(root, "leg_fr");
        this.legBL = find(root, "leg_bl");
        this.legBR = find(root, "leg_br");
        this.legL = find(root, "leg_l");
        this.legR = find(root, "leg_r");
        this.armL = find(root, "arm_l");
        this.armR = find(root, "arm_r");
        this.backpack = find(root, "backpack");
        this.tongue = find(root, "tongue");
        this.scarfTail = find(root, "scarf_tail");
        this.antennaL = find(root, "antenna_l");
        this.antennaR = find(root, "antenna_r");
        this.sproutL = find(root, "sprout_l");
        this.sproutR = find(root, "sprout_r");
        this.hat = find(root, "hat");
        this.hatTip = find(root, "hat_tip");
        this.crest = find(root, "crest");
        this.flower = find(root, "flower");
    }

    /** The part called {@code name} anywhere below {@code part} (depth first), or null. */
    private static @Nullable ModelPart find(ModelPart part, String name) {
        if (part.hasChild(name)) {
            return part.getChild(name);
        }
        for (ModelPart child : part.children.values()) {
            ModelPart hit = find(child, name);
            if (hit != null) {
                return hit;
            }
        }
        return null;
    }

    public ModelPart rootPart() {
        return this.root;
    }

    public ModelPart root() {
        return this.root;
    }

    @Override
    public void setupAnim(TamaPet pet, float limbSwing, float limbSwingAmount, float ageInTicks, float netHeadYaw, float headPitch) {
        PetRenderState s = this.state;
        s.walkAnimationPos = limbSwing;
        s.walkAnimationSpeed = limbSwingAmount;
        s.ageInTicks = ageInTicks;
        s.yRot = netHeadYaw;
        s.xRot = headPitch;
        pose(s);
    }

    /** Poses the model for {@code s} (from the rest pose). */
    public void pose(PetRenderState s) {
        this.state = s;
        this.root.getAllParts().forEach(ModelPart::resetPose);
        PetAnimator.animate(this, s);
    }

    @Override
    public void renderToBuffer(PoseStack poseStack, VertexConsumer buffer, int light, int overlay, int color) {
        this.root.render(poseStack, buffer, light, overlay, color);
    }
}
