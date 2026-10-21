package net.kasax.tamagotchi.client.render;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.client.renderer.entity.state.LivingEntityRenderState;
import net.minecraft.client.renderer.item.ItemStackRenderState;
import net.minecraft.resources.Identifier;
import org.jspecify.annotations.Nullable;

/** Per-frame snapshot of a pet for the model, the animator and the layers. */
@Environment(EnvType.CLIENT)
public class PetRenderState extends LivingEntityRenderState {
    public PetSpecies species = PetSpecies.DESERT_DRAGON;
    public int flags;
    public boolean sitting;
    public boolean tame;
    public boolean swimming;
    public boolean grounded = true;
    public float mood = 70;
    public @Nullable PetAction action;
    public float actionT = -1;
    public String expression = "normal";
    public Identifier texture;
    public @Nullable Identifier glowTexture;
    public final ItemStackRenderState heldItem = new ItemStackRenderState();

    public boolean has(int flag) {
        return (this.flags & flag) != 0;
    }
}
