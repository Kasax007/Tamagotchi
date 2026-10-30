package net.kasax.tamagotchi.item;

import java.util.List;
import java.util.function.Consumer;
import net.kasax.tamagotchi.pet.PetAction;
import net.kasax.tamagotchi.pet.PetNeeds;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModEntities;
import net.kasax.tamagotchi.registry.ModItems;
import net.kasax.tamagotchi.registry.ModParticles;
import net.kasax.tamagotchi.registry.ModSounds;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.ProblemReporter;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.storage.TagValueInput;
import net.minecraft.world.level.storage.TagValueOutput;
import net.minecraft.world.phys.Vec3;
import org.jspecify.annotations.Nullable;

/**
 * A fainted pet. Holds the whole pet (name, needs, bond, backpack, snacks); use it on a block and
 * the pet wakes up again.
 */
public class TamaEggItem extends Item {
    public TamaEggItem(Item.Properties properties) {
        super(properties);
    }

    public static ItemStack fromPet(TamaPet pet) {
        TagValueOutput out = TagValueOutput.createWithContext(ProblemReporter.DISCARDING, pet.registryAccess());
        pet.saveWithoutId(out);
        CompoundTag tag = out.buildResult();
        for (String k : List.of("UUID", "Pos", "Motion", "Rotation", "FallDistance", "fall_distance", "Fire", "Air", "OnGround",
                "leash", "Leash", "HurtTime", "DeathTime", "HurtByTimestamp", "active_effects")) {
            tag.remove(k);
        }
        CompoundTag root = new CompoundTag();
        root.putString("Species", pet.species().id());
        root.putString("Name", pet.getName().getString());
        root.put("Pet", tag);
        ItemStack egg = new ItemStack(ModItems.TAMA_EGG);
        egg.set(DataComponents.CUSTOM_DATA, CustomData.of(root));
        egg.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(pet.species().id()), List.of()));
        egg.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true);
        return egg;
    }

    private static CompoundTag root(ItemStack stack) {
        CustomData data = stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY);
        return data.copyTag();
    }

    @Override
    public Component getName(ItemStack stack) {
        String name = root(stack).getStringOr("Name", "");
        return name.isEmpty() ? super.getName(stack) : Component.translatable("item.tamagotchi.tama_egg.named", name);
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext context, TooltipDisplay display, Consumer<Component> builder, TooltipFlag flag) {
        PetSpecies s = PetSpecies.byId(root(stack).getStringOr("Species", ""));
        if (s != null) {
            builder.accept(s.displayName().copy().withStyle(ChatFormatting.LIGHT_PURPLE));
        }
        builder.accept(Component.translatable("item.tamagotchi.tama_egg.tooltip").withStyle(ChatFormatting.GRAY));
    }

    /** The species inside an egg, or null for a blank one. */
    public static @Nullable PetSpecies species(ItemStack egg) {
        return PetSpecies.byId(root(egg).getStringOr("Species", ""));
    }

    @Override
    public InteractionResult useOn(UseOnContext ctx) {
        if (!(ctx.getLevel() instanceof ServerLevel level)) {
            return InteractionResult.SUCCESS;
        }
        ItemStack stack = ctx.getItemInHand();
        BlockPos pos = ctx.getClickedPos().relative(ctx.getClickedFace());
        if (wake(level, stack, Vec3.atBottomCenterOf(pos), ctx.getRotation() + 180, false) == null) {
            return InteractionResult.FAIL;
        }
        stack.shrink(1);
        return InteractionResult.SUCCESS_SERVER;
    }

    /**
     * Brings the pet in {@code egg} back at {@code at}: with half its health from a plain wake-up, fully healed and
     * rested when it hatches in an incubator. Does not use up the egg.
     */
    public static @Nullable TamaPet wake(ServerLevel level, ItemStack egg, Vec3 at, float yRot, boolean incubated) {
        CompoundTag root = root(egg);
        PetSpecies s = PetSpecies.byId(root.getStringOr("Species", ""));
        if (s == null) {
            return null;
        }
        CompoundTag petTag = root.getCompoundOrEmpty("Pet");
        EntityType<TamaPet> type = ModEntities.type(s);
        Entity e = EntityType.create(type, TagValueInput.create(ProblemReporter.DISCARDING, level.registryAccess(), petTag), level,
                EntitySpawnReason.SPAWN_ITEM_USE).orElse(null);
        if (!(e instanceof TamaPet pet)) {
            return null;
        }
        pet.snapTo(at.x, at.y, at.z, yRot, 0);
        if (incubated) {
            pet.setHealth(pet.getMaxHealth());
            pet.needs().add(PetNeeds.Need.ENERGY, 100);
            pet.needs().add(PetNeeds.Need.FUN, 30);
            pet.needs().addBond(1.0F);
        } else {
            pet.setHealth(Math.max(pet.getHealth(), pet.getMaxHealth() * 0.5F));
        }
        level.addFreshEntity(pet);
        pet.playAction(PetAction.TAMED);
        BlockPos pos = pet.blockPosition();
        level.playSound(null, pos, ModSounds.PET_WAKE, SoundSource.NEUTRAL, 1.0F, 1.0F);
        level.sendParticles(ModParticles.HEART, pet.getX(), pet.getY() + 0.6, pet.getZ(), incubated ? 14 : 8, 0.3, 0.3, 0.3, 0.0);
        level.sendParticles(ParticleTypes.POOF, pet.getX(), pet.getY() + 0.3, pet.getZ(), 10, 0.3, 0.2, 0.3, 0.02);
        pet.syncNeeds();
        return pet;
    }
}
