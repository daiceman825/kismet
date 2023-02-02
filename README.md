# kismet
Collection of Scripts to be used with Kismet

## Trilateration.py 

This python script can provide a rough location of a Wi-Fi Access Point by trilaterating the signal using kismet historical geopoints and the rssi values associated with them. 

### Prerequisite changes
In order for this script to work, the following changes need to be made to the kismet config files:
```
/etc/kismet/kismet_memory.conf
  keep_location_cloud_history=true
```
Additionally, changes can be made to the main config file to limit the amount of channels in the channel-hopping sequence in order to maximize the time spent listening to "relevant" wi-fi channels.
```
/etc/kismet/kismet.conf 
  channel_hop=true
  channels=1,6,11  #<- change this to add any channels to the hop list
  randomized_hopping=false
```

### Installation
```
git clone https://github.com/daiceman825/kismet.git
cd kismet
pip3 install -r requirements.txt
sed -i "s/keep_location_cloud_history=false/keep_location_cloud_history=true/" /etc/kismet/kismet_memory.conf
sed -i "s/channel_hop=true/channel_hop=true\nchannels=1,6,11/" /etc/kismet/kismet.conf
sed -i "s/randomized_hopping=true/randomized_hopping=false/" /etc/kismet/kismet.conf
```

### Usage: 
```
python3 trilaterate.py -f /path/to/file.kismet -t AA:BB:CC:DD:EE:FF
```

The output from this script is a folium map that displays all historical geopoints as red circles, the radius of which is determined by the rssi value measured at that point. It also displays the (roughly) calculated location as a blue circle. See the example below:

![example map output](trilateration-example.png)
