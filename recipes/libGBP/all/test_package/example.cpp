#include <iostream>
#define LIBGBP_NO_BACKWARD_COMPATIBLE_UNITS_NAMESPACES
#include <libGBP/GaussianBeam.hpp>


int main()
{
  GaussianLaserBeam beam;

  beam.setOneOverEWaistDiameter(5 * units::i::mm);
  beam.setOneOverEFullAngleDivergence(1.5 * units::i::mrad);

  // using Catch2
  std::cout << beam.getOneOverEDiameter<units::t::cm>(10 * units::i::m).value() << std::endl;
}
