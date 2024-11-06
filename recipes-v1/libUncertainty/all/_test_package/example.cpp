#include <libUncertainty/uncertain.hpp>

int main()
{
  libUncertainty::uncertain<double> x(3,1);
  std::cout << x << "\n";
}
