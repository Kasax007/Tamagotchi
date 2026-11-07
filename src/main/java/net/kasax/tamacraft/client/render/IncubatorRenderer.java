package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamacraft.Tamacraft;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;
import net.kasax.tamacraft.block.PetIncubatorBlockEntity;
import net.kasax.tamacraft.item.TamaEggItem;
import net.kasax.tamacraft.pet.PetSpecies;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.model.geom.PartPose;
import net.minecraft.client.model.geom.builders.CubeListBuilder;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.model.geom.builders.MeshDefinition;
import net.minecraft.client.model.geom.builders.PartDefinition;
import net.minecraft.util.FastColor;

/** The egg in the incubator: a speckled egg in the pet's colours that wobbles harder the closer it is to hatching. */
@Environment(EnvType.CLIENT)
public class IncubatorRenderer implements BlockEntityRenderer<PetIncubatorBlockEntity> {
    public static final ModelLayerLocation LAYER = new ModelLayerLocation(Tamacraft.id("incubator_egg"), "main");
    private static final ResourceLocation TEXTURE = Tamacraft.id("textures/entity/incubator_egg.png");
    /** Top of the nest inside the dome, in pixels. */
    private static final float NEST_Y = 3F;
    private final ModelPart egg;

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
    public void render(PetIncubatorBlockEntity be, float partialTick, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        if (be.getEgg().isEmpty()) {
            return;
        }
        PetSpecies s = TamaEggItem.species(be.getEgg());
        int color = s != null ? FastColor.ARGB32.opaque(FastColor.ARGB32.lerp(0.35F, s.color(), 0xFFFFFFFF)) : 0xFFF4EEDC;
        float progress = be.progress(partialTick);
        float time = be.getLevel() != null ? (be.getLevel().getGameTime() % 24000) + partialTick : 0;
        poseStack.pushPose();
        poseStack.translate(0.5F, NEST_Y / 16F, 0.5F);
        // a little wobble now and then, faster and wider towards the end
        float p = progress;
        float cycle = Mth.lerp(p, 60, 18);
        float phase = (time % cycle) / cycle;
        float burst = phase < 0.35F ? Mth.sin(phase / 0.35F * Mth.PI) : 0;
        float angle = burst * Mth.sin(time * 1.3F) * Mth.lerp(p, 5, 12);   // more would nick the dome
        poseStack.mulPose(Axis.ZP.rotationDegrees(angle));
        poseStack.mulPose(Axis.XP.rotationDegrees(angle * 0.4F));
        poseStack.scale(-1, -1, 1);   // model space is y down, like an entity model
        this.egg.render(poseStack, buffers.getBuffer(RenderType.entityCutout(TEXTURE)), light, OverlayTexture.NO_OVERLAY, color);
        poseStack.popPose();
    }
}
