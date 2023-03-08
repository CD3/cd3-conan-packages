#include<iostream>
#include <BoostUnitDefinitions/Units.hpp>

int main()
{
  boost::units::quantity<boost::units::t::meter> L(2*boost::units::i::meter);

  std::cout << L << std::endl;
}
