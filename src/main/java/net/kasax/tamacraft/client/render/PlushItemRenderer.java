package net.kasax.tamacraft.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.BlockEntityWithoutLevelRenderer;
import net.kasax.tamacraft.block.PlushBlock;
import net.kasax.tamacraft.pet.PetSpecies;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelPart;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/**
 * The plush items: the same little pet as the placed plush (item model parent builtin/entity, display transforms from
 * tamacraft:item/template_plush). The models are baked on first use, after the entity model layers are loaded.
 */
public class PlushItemRenderer extends BlockEntityWithoutLevelRenderer {
    private PetStatues statues;
    private ModelPart tag;

    /** Made on first use (in game), when the block entity renderers and the entity models exist. */
    public PlushItemRenderer() {
        super(Minecraft.getInstance().getBlockEntityRenderDispatcher(), Minecraft.getInstance().getEntityModels());
    }

    @Override
    public void renderByItem(ItemStack stack, ItemDisplayContext mode, PoseStack poseStack, MultiBufferSource buffers, int light, int overlay) {
        if (!(stack.getItem() instanceof BlockItem item) || !(item.getBlock() instanceof PlushBlock plush)) {
            return;
        }
        if (this.statues == null) {
            var models = Minecraft.getInstance().getEntityModels();
            this.statues = new PetStatues(models::bakeLayer);
            this.tag = models.bakeLayer(PlushTag.LAYER);
        }
        PetSpecies species = plush.species();
        float s = PetStatues.scaleFor(species, PlushRenderer.HEIGHT);
        poseStack.pushPose();
        // the item space of the 26.x special model: (after vanilla's -0.5 shift) translation 0.5 1.5 0.5, scale 1 -1 -1;
        // y down, 24 px = the ground, the plush stands centred on it
        poseStack.translate(0.5F, 1.5F, 0.5F);
        poseStack.scale(1, -1, -1);
        poseStack.translate(0, 1.5F, 0);
        poseStack.scale(s * PlushRenderer.CHUBBY, s * 0.95F, s * PlushRenderer.CHUBBY);
        poseStack.translate(0, -1.5F, 0);
        // PetStatues starts with its own flip into model space (scale -1 -1 1, then down 1.501): undo it, we are there already
        poseStack.translate(0, 1.501F, 0);
        poseStack.scale(-1, -1, 1);
        this.statues.render(species, this.statues.pose(species), poseStack, buffers, light, this.tag);
        poseStack.popPose();
    }
}
