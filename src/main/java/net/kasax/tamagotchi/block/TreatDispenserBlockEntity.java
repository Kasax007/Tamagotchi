package net.kasax.tamagotchi.block;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import net.kasax.tamagotchi.pet.TamaPet;
import net.kasax.tamagotchi.registry.ModBlocks;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.DispenserBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;

/** Nine slots of treats, plus the treats in the air right now (so the pet can catch them). */
public class TreatDispenserBlockEntity extends DispenserBlockEntity {
    private static final Component NAME = Component.translatable("block.tamagotchi.treat_dispenser");
    private static final double RANGE = 12;
    private final List<Flight> flights = new ArrayList<>();

    private record Flight(ItemEntity item, TamaPet pet, long landsAt) {
    }

    public TreatDispenserBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlocks.TREAT_DISPENSER_BE, pos, state);
    }

    @Override
    protected Component getDefaultName() {
        return NAME;
    }

    /** One redstone pulse: one treat for the hungriest pet in range that likes something in here. */
    public void launch(ServerLevel level) {
        Vec3 top = Vec3.atBottomCenterOf(this.worldPosition).add(0, 1.0, 0);
        List<TamaPet> pets = level.getEntitiesOfClass(TamaPet.class, new AABB(this.worldPosition).inflate(RANGE, 6, RANGE),
                p -> p.isTame() && p.isAlive() && !p.isSleeping() && p.needs().hunger < 90);
        pets.sort(Comparator.comparingDouble(p -> p.needs().hunger));
        for (TamaPet pet : pets) {
            int slot = pickSlot(pet);
            if (slot < 0) {
                continue;
            }
            ItemStack treat = removeItem(slot, 1);
            int ticks = (int) Math.clamp(10 + pet.position().distanceTo(top) * 1.6, 12, 28);
            Vec3 aim = pet.position().add(0, pet.getBbHeight() * 0.8, 0).add(pet.getDeltaMovement().scale(ticks * 0.5));
            Vec3 v = velocityFor(aim.subtract(top), ticks);
            ItemEntity item = new ItemEntity(level, top.x, top.y, top.z, treat, v.x, v.y, v.z);
            item.setPickUpDelay(ticks + 40);
            level.addFreshEntity(item);
            this.flights.add(new Flight(item, pet, level.getGameTime() + ticks));
            pet.getNavigation().stop();
            pet.getLookControl().setLookAt(item, 30, 30);
            level.playSound(null, this.worldPosition, SoundEvents.DISPENSER_LAUNCH, SoundSource.BLOCKS, 0.6F, 1.7F);
            setChanged();
            return;
        }
        level.playSound(null, this.worldPosition, SoundEvents.DISPENSER_FAIL, SoundSource.BLOCKS, 0.6F, 1.4F);
    }

    /** The pet's favourite treat if it is in here, else any food it eats; -1 when there is none. */
    private int pickSlot(TamaPet pet) {
        int any = -1;
        for (int i = 0; i < getContainerSize(); i++) {
            ItemStack s = getItem(i);
            if (s.isEmpty() || !pet.isPetFood(s)) {
                continue;
            }
            if (s.is(pet.species().favoriteTreat())) {
                return i;
            }
            if (any < 0) {
                any = i;
            }
        }
        return any;
    }

    /** Launch velocity of an item entity that is at {@code d} after {@code ticks} (gravity 0.04, drag 0.98 per tick). */
    static Vec3 velocityFor(Vec3 d, int ticks) {
        double sum = 0;   // sum of 0.98^k: distance per unit of start speed
        double fall = 0;  // where a dropped item would be
        double vy = 0;
        double f = 1;
        for (int k = 0; k < ticks; k++) {
            sum += f;
            f *= 0.98;
            vy -= 0.04;
            fall += vy;
            vy *= 0.98;
        }
        return new Vec3(d.x / sum, (d.y - fall) / sum, d.z / sum);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, TreatDispenserBlockEntity be) {
        if (be.flights.isEmpty()) {
            return;
        }
        long now = level.getGameTime();
        be.flights.removeIf(f -> {
            if (!f.item.isAlive() || !f.pet.isAlive() || now > f.landsAt + 40) {
                return true;
            }
            f.pet.getLookControl().setLookAt(f.item, 30, 30);
            if (f.landsAt - now == 5 && f.pet.onGround()) {
                f.pet.getJumpControl().jump();
            }
            boolean caught = f.pet.getBoundingBox().inflate(0.35).intersects(f.item.getBoundingBox());
            boolean onFloorNearby = now > f.landsAt + 10 && f.pet.distanceTo(f.item) < 2.5;
            if (!caught && !onFloorNearby) {
                return false;
            }
            ItemStack one = f.item.getItem().split(1);
            if (f.item.getItem().isEmpty()) {
                f.item.discard();
            }
            f.pet.eat(one);
            if (one.is(f.pet.species().favoriteTreat())) {
                f.pet.needs().addBond(1.0F);
                f.pet.needs().add(net.kasax.tamagotchi.pet.PetNeeds.Need.FUN, 6);
                f.pet.syncNeeds();
            }
            return true;
        });
    }
}
