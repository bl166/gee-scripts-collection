'''
cropPowerPlants.py

This script works on the Google Earth Engine (Python API). It reads geographic coordinates of US power plants 
in 2014 egrid document, and gets the recanglular region (.005 degrees on each span) centered at it. It primarily 
works on NAIP and Landsat8 data, but will take whatever imagery that is correctly imported. 

Duke Data+ 2017: Electricity Access
Jul 26, 2017
'''

# Import the Earth Engine Python Package
import ee
from xlrd import open_workbook

ee.Initialize();
# Function to download powerplant pictures
# takes 2 arguments: [id_start, id_end)
def download_ppt_pic(id_start,id_end,option):
	# open the document with coordinates of US power plants
	egrid = open_workbook("egrid2014_data_v2_PLNT14.xlsx").sheet_by_index(0) # if your data is on sheet 1
 
	# DEFINE YOUR IMAGE COLLECTION HERE
	#************** NAIP imagery **************
	if option=='naip':
		collection_naip = ee.ImageCollection('USDA/NAIP/DOQQ').filter(ee.Filter.date('2012-01-01', '2014-12-31'))
		# reduce the image stack to one image
		image = collection_naip.mosaic()
		# resolution = 1m
		res = 1

	#********** Pan-sharpened Landsat **********
	elif option=='ls8':
		collection_ls8 = ee.ImageCollection('LANDSAT/LC8_L1T_TOA').filterDate('2014-01-01', '2014-12-30')
		# reduce the image stack to every pixel's median value
		img_red = collection_ls8.reduce(ee.Reducer.median())
		# pan sharpening by hsv & panchromatic band
		rgb = img_red.select('B4_median', 'B3_median', 'B2_median')
		gray = img_red.select('B8_median')
		huesat = rgb.rgbToHsv().select('hue', 'saturation')
		image = ee.Image.cat(huesat, gray).hsvToRgb()
		# resolution = 15m
		res = 15

	else:
		print('Cannot find '+option+' collections. Please choose between \'naip\' and \'ls8\'.')

	# the span to crop
	deg = .005
 
	 # Each ID defines a unique power plant in egrid document
	for pid_int in range(id_start, id_end):
		# find which one it is
		row = egrid.col_values(0).index(pid_int)
		try:
			# set the region to crop
			geometry = ee.Geometry.Rectangle([
				float(egrid.cell_value(row,5))-deg, # longtitude lower bound
				float(egrid.cell_value(row,4))-deg, # latitude lower bound
				float(egrid.cell_value(row,5))+deg, # longtitude upper bound
				float(egrid.cell_value(row,4))+deg  # latitude upper bound
			]);
			roi=image.clip(geometry)
 
			# configurations for export
			config_d = {
				'scale': res,					 # resolution
				'skipEmptyTiles': True,		 	 # action flag
				'maxPixels':1E9,				 # max: 1E13 
				'folder': 'PowerPlants_'+option  # destination
			}

			# define and start the task
			task = ee.batch.Export.image(roi, str(pid_int), config=config_d)
			task.start()

			print(str(pid_int)+':'+option)

		except ValueError:
			print(-1)


if __name__ == '__main__':
	id_start,id_end = (300,500)
	download_ppt_pic(id_start,id_end,'naip')
	download_ppt_pic(id_start,id_end,'ls8')

