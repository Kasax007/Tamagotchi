package net.kasax.tamagotchi.client.render;

import com.mojang.blaze3d.vertex.PoseStack;
import java.util.HashMap;
import java.util.Map;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.Tamagotchi;
import net.kasax.tamagotchi.client.model.PetModel;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.minecraft.client.Minecraft;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.MobRenderer;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.ItemDisplayContext;
import org.jspecify.annotations.Nullable;

/** Renders every pet: generated model, expression textures, glow layer and a carried toy. */
@Environment(EnvType.CLIENT)
public class PetRenderer extends MobRenderer<TamaPet, PetRenderState, PetModel> {
    public static final float MODEL_SCALE = 0.8F;
    private static final Map<Identifier, Boolean> EXISTS = new HashMap<>();
    private final PetSpecies species;

    public PetRenderer(EntityRendererProvider.Context ctx, PetSpecies species, ModelLayerLocation layer) {
        super(ctx, new PetModel(ctx.bakeLayer(layer), species), species.width() * 0.55F);
        this.species = species;
        addLayer(new PetGlowLayer(this));
        addLayer(new PetHeldItemLayer(this));
    }

    @Override
    public PetRenderState createRenderState() {
        return new PetRenderState();
    }

    @Override
    public void extractRenderState(TamaPet pet, PetRenderState state, float partialTick) {
        super.extractRenderState(pet, state, partialTick);
        state.species = this.species;
        state.flags = pet.syncedFlags();
        state.sitting = pet.isInSittingPose();
        state.tame = pet.isTame();
        state.swimming = pet.isInWater() && !pet.onGround();
        state.grounded = pet.onGround();
        state.mood = pet.syncedMoodValue();
        float t = pet.actionProgress(partialTick);
        state.action = t >= 0 ? pet.clientAction : null;
        state.actionT = t;
        state.expression = expression(pet, state);
        state.texture = TamaPet.texture(this.species, state.expression);
        state.glowTexture = glowFor(state.expression);
        this.itemModelResolver.updateForLiving(state.heldItem, pet.getCarried(), ItemDisplayContext.GROUND, pet);
    }

    private static String expression(TamaPet pet, PetRenderState s) {
        if (s.has(TamaPet.F_SLEEPING)) {
            return "sleep";
        }
        PetAction a = s.action;
        if (a == PetAction.PETTED || a == PetAction.TAMED || a == PetAction.GROOMED) {
            return s.actionT < 0.6F ? "love" : "happy";
        }
        if (a == PetAction.EAT || a == PetAction.CELEBRATE || a == PetAction.PLAY || a == PetAction.BOUNCE
                || a == PetAction.FEED_OWNER) {
            return "happy";
        }
        if (a == PetAction.YAWN) {
            return "sleep";
        }
        if (s.has(TamaPet.F_AGGRESSIVE) || a == PetAction.ATTACK || a == PetAction.BREATH) {
            return "angry";
        }
        if (s.has(TamaPet.F_SCARED)) {
            return "sad";
        }
        if (s.has(TamaPet.F_DANCING) || s.has(TamaPet.F_WARMING) || s.has(TamaPet.F_RUNNING)) {
            return pet.tickCount < pet.blinkUntil ? "blink" : "happy";
        }
        if (pet.tickCount < pet.blinkUntil) {
            return "blink";
        }
        if (s.tame && s.mood < 25) {
            return "sad";
        }
        return "normal";
    }

    private @Nullable Identifier glowFor(String expr) {
        Identifier specific = Tamagotchi.id("textures/entity/" + this.species.id() + "/" + this.species.id() + "_glow_" + expr + ".png");
        if (exists(specific)) {
            return specific;
        }
        Identifier base = Tamagotchi.id("textures/entity/" + this.species.id() + "/" + this.species.id() + "_glow.png");
        return exists(base) ? base : null;
    }

    private static boolean exists(Identifier id) {
        return EXISTS.computeIfAbsent(id, i -> Minecraft.getInstance().getResourceManager().getResource(i).isPresent());
    }

    public static void clearCache() {
        EXISTS.clear();
    }

    @Override
    public Identifier getTextureLocation(PetRenderState state) {
        return state.texture;
    }

    @Override
    protected void scale(PetRenderState state, PoseStack poseStack) {
        float s = MODEL_SCALE * (state.isBaby ? 0.6F : 1F);
        poseStack.scale(s, s, s);
    }
}
