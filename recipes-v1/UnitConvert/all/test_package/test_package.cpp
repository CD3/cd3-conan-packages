#include <iostream>
#include <UnitConvert.hpp>



int main(void) {

  UnitRegistry ureg;
  ureg.addUnit("m = [L]");

  auto x = ureg.makeQuantity<double>(2,"m");

  std::cout << x << std::endl;

  return EXIT_SUCCESS;
}
