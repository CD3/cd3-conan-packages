#! /bin/bash

conan remove -f libField/master@cd3/devel
conan remove -f libIntegrate/master@cd3/devel
conan remove -f libInterpolate/master@cd3/devel



rm demo_sandbox -rf
mkdir demo_sandbox
cd demo_sandbox
mkdir integrator
cd integrator
cat << 'EOF' > main.cpp

#include <iostream>

#include <Integrate.hpp>
#include <Interp.hpp>
#include <Field.hpp>

#include <vector>

int main()
{

  Field<double,1> f(10);
  f.setCoordinateSystem( Uniform(0,M_PI) );
  f.set_f( []( auto x ){ return sin(x[0]); } );

  _1D::GQ::GaussLegendreQuadrature<double,16> integrate;
  _1D::CubicSplineInterpolator<double> interp;

  interp.setData( f.getAxis(0), f.getData() );


  double ans = integrate( interp, 0., M_PI );
  
  std::cout << "Exact Answer: 2" << std::endl;
  std::cout << "Numerical Approximation: " << ans << std::endl;


}
EOF

cat << 'EOF' > CMakeLists.txt
cmake_minimum_required( VERSION 3.10 )

find_package( libField REQUIRED )
find_package( libIntegrate REQUIRED )
find_package( libInterp REQUIRED )

add_executable( compute-integral main.cpp )
target_link_libraries( compute-integral libField::Field libIntegrate::Integrate libInterp::Interp )
EOF

