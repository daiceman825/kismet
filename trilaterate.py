import kismetdb 
import json
import numpy as np 
from scipy.optimize import least_squares
import folium
import sys, getopt
import math
from math import sin, cos, sqrt, atan2

# create space so that
print("\n\n\n")

# Haversine distance formula, used to get the distance between two geopoints in meters
def distance_in_m(lat1, lon1, lat2, lon2): 
    R = 6372800  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))

# create a circle for every geopoint
# radius of the circle corresponds with the rssi value measured at that geopoint
# get the intersection points for each circle at i and i+1 to average them in the following way:
# 1&2 , 2&3 , 3&4 , ... for N amount of circles. 
# take the average of all the intersection points and return that point as a geopoint.
def circle_intersection(latitudes, longitudes, distances):
    n = len(latitudes)
    x = 0
    y = 0
    num_intersections = 0
    for i in range(n-1):
        for j in range(i+1, n):
            lat1, lon1, d1 = latitudes[i], longitudes[i], distances[i]
            lat2, lon2, d2 = latitudes[j], longitudes[j], distances[j]
            d = distance_in_m(lat1, lon1, lat2, lon2)
            if d > (d1 + d2):
                continue
            elif d < abs(d1 - d2):
                continue
            elif d == 0:
                continue
            else:
                a = (d1*d1 - d2*d2 + d*d) / (2*d)
                h = sqrt(d1*d1 - a*a)
                x0 = lat1 + a*(lat2 - lat1) / d
                y0 = lon1 + a*(lon2 - lon1) / d
                xi = x0 + h*(lon2 - lon1) / d
                yi = y0 - h*(lat2 - lat1) / d
                x += xi
                y += yi
                num_intersections += 1
    if num_intersections == 0:
        print("Cannot calculate. Not enough intersections.")
        return 0
    else:
        return x/num_intersections, y/num_intersections

# function to calculate distance from RSSI using the inverse square law
def calculate_distance(rssi, frequency):
	# frequency in KHz (pulled straight from kismet)
    path_loss_exponent = 3.14159 # pi! 
    # NEW method using Log-Distance Path Loss and additional tweaks
    distance = (10**((27.55-(20*np.log10(frequency))+np.fabs(rssi))/(20*path_loss_exponent)))*200
    return distance-30 # in meters. subtracted 30 for accuracy. not sure why

# plot it on a map using folium
def plot_map(lons, lats, rssis, freq, mappy):
    map_ = mappy
    for i in range(len(lons)):
        lat, lon = lats[i], lons[i]
        distance = calculate_distance(rssis[i], freq)
        folium.Circle(location=[lat, lon], radius=distance, color='red', fill=False, fill_color='red').add_to(map_)
    return map_


def main(argv):
	target_SSID = ''
	search_all = True
	try:
		opts, args = getopt.getopt(argv,"hf:t:",["file=","target="])
	except getopt.GetoptError:
		print("You must supply the following arguments:")
		print("-f : kismet file to parse")
		print("-t : Target SSID")
		print('trilaterate.py -f infile.kismet -t AA:BB:CC:DD:EE:FF')
		sys.exit(2)
	for opt, arg in opts:
		if opt == '-h':
			print('trilaterate.py -f infile.kismet -t AA:BB:CC:DD:EE:FF')
			sys.exit(0)
		elif opt in '-f':
			devices = kismetdb.Devices(arg)
		elif opt in '-t':
			target_SSID = arg
			search_all = False
	
	if search_all :
		print("please specify a target mac address.")
		sys.exit(0)
	elif not search_all:
		print("searching for " + target_SSID)
		all_devs = devices.yield_all(type="Wi-Fi AP",devmac=target_SSID)
	else:
		print("I'm not sure how you got this error")
	
	for device in all_devs:
		freq = json.loads(device["device"])["kismet.device.base.frequency"]	
		
		samples = ''
		try:
			samples = json.loads(device["device"])["kismet.device.base.location_cloud"]["kis.gps.rrd.samples_100"]
		except:
			next # do nothing, skip to next device
		
		lons = []
		lats = []
		rssis = []
		sample_count = 0
		for s in samples:
			sample_count += 1
			try:
				lons.append(s['kismet.historic.location.geopoint'][0])
				lats.append(s['kismet.historic.location.geopoint'][1])
				rssis.append(s['kismet.historic.location.signal'])
			except: 
				continue
		if sample_count >= 3:
			distances = [ calculate_distance(x,freq) for x in rssis ]
			if circle_intersection(lats, lons, distances) == 0:
				next # device in list
			else:
				print("trying to plot...")
				lat, lon = circle_intersection(lats, lons, distances)
				da_map = folium.Map(location=[lat,lon],zoom_start=17)
				da_map = plot_map(lons, lats, rssis, freq, da_map)
				folium.Circle(location=[lat, lon], radius=25, color='blue', fill=False, fill_color='blue').add_to(da_map)
				da_map.show_in_browser()
		else:
			print("Not enough historical samples.")
			continue # do nothing...


if __name__ == "__main__":
   main(sys.argv[1:])
