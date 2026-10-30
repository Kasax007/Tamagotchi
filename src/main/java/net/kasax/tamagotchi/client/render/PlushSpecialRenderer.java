package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.serialization.Codec;
import com.mojang.serialization.DataResult;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.function.Consumer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.client.TamagotchiClient;
import net.kasax.tamagotchi.client.model.PetModel;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.special.NoDataSpecialModelRenderer;
import net.minecraft.client.renderer.special.SpecialModelRenderer;
import org.joml.Vector3f;
import org.joml.Vector3fc;

/** The plush items: the same little pet as the placed plush (item model type tamagotchi:plush). */
@Environment(EnvType.CLIENT)
public class PlushSpecialRenderer implements NoDataSpecialModelRenderer {
    private final PetSpecies species;
    private final PetModel model;
    private final PetRenderState pose = new PetRenderState();
    private final ModelPart tag;
    private final Vector3f tagAt;

    public PlushSpecialRenderer(PetSpecies species, PetModel model, ModelPart tag) {
        this.species = species;
        this.model = model;
        this.tag = tag;
        this.pose.species = species;
        this.pose.sitting = true;
        this.pose.tame = true;
        this.pose.expression = "happy";
        this.pose.texture = TamaPet.texture(species, "happy");
        this.tagAt = PlushTag.anchor(model, this.pose);
    }

    /** Item space (after the definition's flip): y down, 24 px = the ground; the plush stands centred on it. */
    private void place(PoseStack poseStack) {
        float s = PetStatues.scaleFor(this.species, PlushRenderer.HEIGHT);
        poseStack.translate(0, 1.5F, 0);
        poseStack.scale(s * PlushRenderer.CHUBBY, s * 0.95F, s * PlushRenderer.CHUBBY);
        poseStack.translate(0, -1.5F, 0);
    }

    @Override
    public void submit(PoseStack poseStack, SubmitNodeCollector collector, int lightCoords, int overlayCoords, boolean hasFoil, int outlineColor) {
        poseStack.pushPose();
        place(poseStack);
        collector.submitModel(this.model, this.pose, poseStack, this.model.renderType(this.pose.texture), lightCoords, overlayCoords, outlineColor);
        PlushTag.submit(this.tag, this.tagAt, poseStack, collector, lightCoords, outlineColor);
        poseStack.popPose();
    }

    @Override
    public void getExtents(Consumer<Vector3fc> output) {
        PoseStack poseStack = new PoseStack();
        place(poseStack);
        this.model.setupAnim(this.pose);
        this.model.root().getExtentsForGui(poseStack, output);
    }

    @Environment(EnvType.CLIENT)
    public record Unbaked(PetSpecies species) implements NoDataSpecialModelRenderer.Unbaked {
        private static final Codec<PetSpecies> SPECIES = Codec.STRING.comapFlatMap(id -> {
            PetSpecies s = PetSpecies.byId(id);
            return s != null ? DataResult.success(s) : DataResult.error(() -> "Unknown pet: " + id);
        }, PetSpecies::id);
        public static final MapCodec<Unbaked> MAP_CODEC = RecordCodecBuilder.mapCodec(
                i -> i.group(SPECIES.fieldOf("species").forGetter(Unbaked::species)).apply(i, Unbaked::new));

        @Override
        public MapCodec<Unbaked> type() {
            return MAP_CODEC;
        }

        @Override
        public PlushSpecialRenderer bake(SpecialModelRenderer.BakingContext context) {
            PetModel model = new PetModel(context.entityModelSet().bakeLayer(TamagotchiClient.LAYERS.get(this.species)), this.species);
            return new PlushSpecialRenderer(this.species, model, context.entityModelSet().bakeLayer(PlushTag.LAYER));
        }
    }
}
