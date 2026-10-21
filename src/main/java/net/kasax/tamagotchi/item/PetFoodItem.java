package net.kasax.tamagotchi.item;

import java.util.function.Consumer;
import net.kasax.tamagotchi.pet.PetSpecies;
import net.kasax.tamagotchi.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;

/** Pet kibble and the favourite treats. Feed by right-clicking a pet, or fill a food bowl. */
public class PetFoodItem extends Item {
    public PetFoodItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext context, TooltipDisplay display, Consumer<Component> builder, TooltipFlag flag) {
        if (stack.is(ModItems.PET_KIBBLE)) {
            builder.accept(Component.translatable("item.tamagotchi.pet_kibble.tooltip").withStyle(ChatFormatting.GRAY));
            return;
        }
        MutableComponent fans = null;
        for (PetSpecies s : PetSpecies.values()) {
            if (stack.is(s.favoriteTreat())) {
                fans = fans == null ? s.displayName().copy() : fans.append(", ").append(s.displayName());
            }
        }
        if (fans != null) {
            builder.accept(Component.translatable("tooltip.tamagotchi.favorite_of", fans).withStyle(ChatFormatting.LIGHT_PURPLE));
        }
    }
}
