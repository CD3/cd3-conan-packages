#include <libUncertainty/uncertain.hpp>
using namespace libUncertainty;

int main()
{
  uncertain<double> x(10,2);

  std::cout << x << std::endl;
}
