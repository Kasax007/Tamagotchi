package net.kasax.tamagotchi.client.render;

import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import org.jetbrains.annotations.Nullable;

/**
 * Per-frame snapshot of a pet for the model, the animator and the layers. Minecraft 1.21.1 has no entity render
 * states, so the renderer fills this in itself (the fields are named like the later vanilla ones).
 */
@Environment(EnvType.CLIENT)
public class PetRenderState {
    public float ageInTicks;
    public float walkAnimationPos;
    public float walkAnimationSpeed;
    /** Head yaw relative to the body and head pitch, in degrees. */
    public float yRot;
    public float xRot;
    public boolean isBaby;
    public boolean isInvisible;

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
    public ResourceLocation texture;
    public @Nullable ResourceLocation glowTexture;
    public ItemStack heldItem = ItemStack.EMPTY;

    public boolean has(int flag) {
        return (this.flags & flag) != 0;
    }
}
