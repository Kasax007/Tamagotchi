package net.kasax.tamagotchi.client.model;

import java.util.function.Function;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.render.PetRenderState;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.client.model.EntityModel;
import net.minecraft.client.model.geom.ModelPart;
import org.jspecify.annotations.Nullable;

/**
 * One model class for every pet. The geometry comes from the generated {@link PetModels}
 * layers; all motion is done by {@link PetAnimator}, which works on bone names, so any pet that
 * has e.g. a "tail" bone gets tail animations for free.
 */
@Environment(EnvType.CLIENT)
public class PetModel extends EntityModel<PetRenderState> {
    final PetSpecies species;
    final @Nullable ModelPart body, head, jaw, earL, earR, tail, tail2, tail3, wingL, wingR;
    final @Nullable ModelPart legFL, legFR, legBL, legBR, legL, legR, armL, armR;
    final @Nullable ModelPart backpack, tongue, scarfTail, antennaL, antennaR, sproutL, sproutR, hat, hatTip, crest, flower;

    public PetModel(ModelPart root, PetSpecies species) {
        super(root);
        this.species = species;
        Function<String, @Nullable ModelPart> p = root.createPartLookup();
        this.body = p.apply("body");
        this.head = p.apply("head");
        this.jaw = p.apply("jaw");
        this.earL = p.apply("ear_l");
        this.earR = p.apply("ear_r");
        this.tail = p.apply("tail");
        this.tail2 = p.apply("tail2");
        this.tail3 = p.apply("tail3");
        this.wingL = p.apply("wing_l");
        this.wingR = p.apply("wing_r");
        this.legFL = p.apply("leg_fl");
        this.legFR = p.apply("leg_fr");
        this.legBL = p.apply("leg_bl");
        this.legBR = p.apply("leg_br");
        this.legL = p.apply("leg_l");
        this.legR = p.apply("leg_r");
        this.armL = p.apply("arm_l");
        this.armR = p.apply("arm_r");
        this.backpack = p.apply("backpack");
        this.tongue = p.apply("tongue");
        this.scarfTail = p.apply("scarf_tail");
        this.antennaL = p.apply("antenna_l");
        this.antennaR = p.apply("antenna_r");
        this.sproutL = p.apply("sprout_l");
        this.sproutR = p.apply("sprout_r");
        this.hat = p.apply("hat");
        this.hatTip = p.apply("hat_tip");
        this.crest = p.apply("crest");
        this.flower = p.apply("flower");
    }

    public ModelPart rootPart() {
        return this.root;
    }

    @Override
    public void setupAnim(PetRenderState state) {
        super.setupAnim(state);
        PetAnimator.animate(this, state);
    }
}
