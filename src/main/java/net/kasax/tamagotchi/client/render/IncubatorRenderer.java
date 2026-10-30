package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.block.PetIncubatorBlockEntity;
import net.kasax.tamagotchi.item.TamaEggItem;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.ARGB;
import net.minecraft.util.Mth;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/** The egg in the incubator: a speckled egg in the pet's colours that wobbles harder the closer it is to hatching. */
@Environment(EnvType.CLIENT)
public class IncubatorRenderer implements BlockEntityRenderer<PetIncubatorBlockEntity, IncubatorRenderer.State> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Tamagotchi.id("incubator_egg"), "main");
    private static final Identifier TEXTURE = Tamagotchi.id("textures/entity/incubator_egg.png");
    /** Top of the nest inside the dome, in pixels. */
    private static final float NEST_Y = 3F;
    private final ModelPart egg;

    public static class State extends BlockEntityRenderState {
        boolean hasEgg;
        int color;
        float progress;
        float time;
    }

    public IncubatorRenderer(BlockEntityRendererProvider.Context ctx) {
        this.egg = ctx.bakeLayer(LAYER);
    }

    /** A voxel egg, 6 px wide and 8 px tall, standing on its own origin (entity-model style: y down, so up is -y). */
    public static LayerDefinition createLayer() {
        MeshDefinition mesh = new MeshDefinition();
        PartDefinition root = mesh.getRoot();
        root.addOrReplaceChild("bottom", CubeListBuilder.create().texOffs(0, 16).addBox(-2, -1, -2, 4, 1, 4), PartPose.ZERO);
        root.addOrReplaceChild("belly", CubeListBuilder.create().texOffs(0, 0).addBox(-3, -5, -3, 6, 4, 6), PartPose.ZERO);
        root.addOrReplaceChild("upper", CubeListBuilder.create().texOffs(0, 10).addBox(-2, -7, -2, 4, 2, 4), PartPose.ZERO);
        root.addOrReplaceChild("tip", CubeListBuilder.create().texOffs(16, 10).addBox(-1, -8, -1, 2, 1, 2), PartPose.ZERO);
        return LayerDefinition.create(mesh, 32, 32);
    }

    @Override
    public State createRenderState() {
        return new State();
    }

    @Override
    public void extractRenderState(PetIncubatorBlockEntity be, State state, float partialTick, Vec3 camera,
                                   ModelFeatureRenderer.@Nullable CrumblingOverlay crumbling) {
        BlockEntityRenderer.super.extractRenderState(be, state, partialTick, camera, crumbling);
        state.hasEgg = !be.getEgg().isEmpty();
        PetSpecies s = state.hasEgg ? TamaEggItem.species(be.getEgg()) : null;
        state.color = s != null ? ARGB.opaque(ARGB.srgbLerp(0.35F, s.color(), 0xFFFFFFFF)) : 0xFFF4EEDC;
        state.progress = be.progress(partialTick);
        state.time = be.getLevel() != null ? (be.getLevel().getGameTime() % 24000) + partialTick : 0;
    }

    @Override
    public void submit(State state, PoseStack poseStack, SubmitNodeCollector collector, CameraRenderState camera) {
        if (!state.hasEgg) {
            return;
        }
        poseStack.pushPose();
        poseStack.translate(0.5F, NEST_Y / 16F, 0.5F);
        // a little wobble now and then, faster and wider towards the end
        float p = state.progress;
        float cycle = Mth.lerp(p, 60, 18);
        float phase = (state.time % cycle) / cycle;
        float burst = phase < 0.35F ? Mth.sin(phase / 0.35F * Mth.PI) : 0;
        float angle = burst * Mth.sin(state.time * 1.3F) * Mth.lerp(p, 5, 12);   // more would nick the dome
        poseStack.rotateDegrees(Axis.ZP, angle);
        poseStack.rotateDegrees(Axis.XP, angle * 0.4F);
        poseStack.scale(-1, -1, 1);   // model space is y down, like an entity model
        collector.submitModelPart(this.egg, poseStack, RenderTypes.entityCutout(TEXTURE), state.lightCoords, OverlayTexture.NO_OVERLAY,
                null, state.color);
        poseStack.popPose();
    }
}
