# pyTopRes
Handy tool to rapidly add topography informations from an Excel spreadsheet to multiple raw geoelectrical tomography data in Res2dInv format (.dat)

dependecies:
re
os
argparse
csv
sys
pandas

python pytopres.py -h
usage: pytopres [-h] [-c COORDINATES] [-f [FILES ...]] [-w WATER WATER]
                [-l LIMITS LIMITS]

Add topography coordinates in Res2DInv format .dat file. Indicated for lazy
applied geophysicist.

options:
  -h, --help            show this help message and exit
  -c COORDINATES, --coordinates COORDINATES
                        a .xlsx table with the followings columns: fid; name;
                        distance (between electrodes, in m); x; y; z. The
                        order may vary and the decimal separator must be dot
  -f [FILES ...], --files [FILES ...]
                        files you want to add topography (*\.dat if you want
                        all .dat files)[mandatory]
  -w WATER WATER, --water WATER WATER
                        insert the water resistivity [arg1] and chargeability
                        [arg2] if you want a water layer above topography
                        [optional]
  -l LIMITS LIMITS, --limits LIMITS LIMITS
                        insert the water layer horizontal limits, e.g.
                        distance from coastline if present [optional]

by Geol. Marco Re, Teglio Veneto, VE, ITALY
