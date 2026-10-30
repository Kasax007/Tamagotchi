package net.kasax.tamagotchi.block;

import java.util.UUID;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.UUIDUtil;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.TagValueOutput;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/** Who is in the picture: the pet's kind, name and id (the id only so the next click paints another pet). */
public class PetPortraitBlockEntity extends BlockEntity {
    private @Nullable PetSpecies species;
    private String name = "";
    private @Nullable UUID petId;
    private boolean backpack;

    public PetPortraitBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.PET_PORTRAIT_BE, pos, state);
    }

    public @Nullable PetSpecies species() {
        return this.species;
    }

    public String name() {
        return this.name;
    }

    public @Nullable UUID petId() {
        return this.petId;
    }

    public boolean backpack() {
        return this.backpack;
    }

    public void paint(TamaPet pet) {
        this.species = pet.species();
        this.name = pet.getName().getString();
        this.petId = pet.getUUID();
        this.backpack = pet.hasFlag(TamaPet.F_BACKPACK);
        setChanged();
        if (this.level != null) {
            this.level.sendBlockUpdated(this.worldPosition, getBlockState(), getBlockState(), Block.UPDATE_ALL);
        }
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        this.species = PetSpecies.byId(input.getStringOr("species", ""));
        this.name = input.getStringOr("name", "");
        this.petId = input.read("pet", UUIDUtil.CODEC).orElse(null);
        this.backpack = input.getBooleanOr("backpack", false);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        if (this.species != null) {
            output.putString("species", this.species.id());
            output.putString("name", this.name);
            output.putBoolean("backpack", this.backpack);
        }
        if (this.petId != null) {
            output.store("pet", UUIDUtil.CODEC, this.petId);
        }
    }

    @Override
    public ClientboundBlockEntityDataPacket getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        TagValueOutput out = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, registries);
        saveAdditional(out);
        return out.buildResult();
    }
}
