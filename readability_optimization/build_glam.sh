module load StdEnv/2020 gcc/9.3.0 boost/1.72.0 cgal/4.14.3 tbb/2020.2
rm -rf glam
git clone https://github.com/kwonoh/glam.git
cd glam
cp ../database/placeholder placeholder
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release; make