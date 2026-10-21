package net.kasax.tamagotchi.pet;

import net.minecraft.util.Mth;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.control.MoveControl;

/** Tide Dragon: swims in 3D like a turtle while in water, walks normally on land. */
public class PetSwimMoveControl extends MoveControl<TamaPet> {
    public PetSwimMoveControl(TamaPet pet) {
        super(pet);
    }

    @Override
    public void tick() {
        if (!this.mob.isInWater()) {
            super.tick();
            return;
        }
        this.mob.setDeltaMovement(this.mob.getDeltaMovement().add(0.0, 0.004, 0.0));
        if (this.operation == MoveControl.Operation.MOVE_TO && !this.mob.getNavigation().isDone()) {
            double xd = this.wantedX - this.mob.getX();
            double yd = this.wantedY - this.mob.getY();
            double zd = this.wantedZ - this.mob.getZ();
            double dd = Math.sqrt(xd * xd + yd * yd + zd * zd);
            if (dd < 1.0E-5F) {
                this.mob.setSpeed(0.0F);
                return;
            }
            yd /= dd;
            float yRot = (float) (Mth.atan2(zd, xd) * 180.0F / (float) Math.PI) - 90.0F;
            this.mob.setYRot(this.rotlerp(this.mob.getYRot(), yRot, 20.0F));
            this.mob.yBodyRot = this.mob.getYRot();
            float target = (float) (this.speedModifier * this.mob.getAttributeValue(Attributes.MOVEMENT_SPEED)) * 2.6F;
            this.mob.setSpeed(Mth.lerp(0.15F, this.mob.getSpeed(), target));
            this.mob.setDeltaMovement(this.mob.getDeltaMovement().add(0.0, this.mob.getSpeed() * yd * 0.12, 0.0));
        } else {
            this.mob.setSpeed(0.0F);
        }
    }
}
