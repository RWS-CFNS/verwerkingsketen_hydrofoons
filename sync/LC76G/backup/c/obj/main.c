#include <stdio.h>      //printf()
#include <stdlib.h>     //exit()
#include <signal.h>

 #include <stdio.h>
 #include <string.h>

#include "DEV_Config.h"
#include "L76X.h"

#include <chrono>
#include <ctime>
#include <iostream>

void  Handler(int signo)
{
    //System Exit
    printf("\r\nHandler:Program stop\r\n"); 

    DEV_ModuleExit();

    exit(0);
}

int main(int argc, char **argv)
{
    GNRMC GPS;
    // Coordinates Baidu;
    
	if (DEV_ModuleInit()==1)return 1;
    // Exception handling:ctrl + c
    
    signal(SIGINT, Handler);

    DEV_Delay_ms(100); 
    DEV_Set_Baudrate(115200);
    DEV_Delay_ms(100);

    printf("hey");

    while(1){
        GPS = L76X_Gat_GNRMC();
        auto now = std::chrono::high_resolution_clock::now();
        auto since_epoch = now.time_since_epoch();
        
        auto now_s  = std::chrono::duration_cast<std::chrono::seconds>(since_epoch);
        auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(since_epoch);
        auto now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(since_epoch);
        
        std::time_t raw_time = now_s.count();
        std::tm* ptm = std::localtime(&raw_time);
        long nanosec_part = now_ns.count() % 1000000000;
        
        if (GPS.Status == 0)
            continue;
        printf("\r\n");
        // printf("Status: %d\r\n", GPS.Status);
        printf("Latitude and longitude: %lf  %c  %lf  %c\r\n", GPS.Lat, GPS.Lat_area, GPS.Lon, GPS.Lon_area);
        printf("GPS Time: %02d:%02d:%02d \r\n", GPS.Time_H + 2, GPS.Time_M, GPS.Time_S);
        printf("GPS Time: %d\r\n", GPS.Time);
        printf("System Time: %02d:%02d:%02d %ld.%09ld\r\n",
               ptm->tm_hour, ptm->tm_min, ptm->tm_sec,
               now_s.count(), nanosec_part);
    }
	DEV_ModuleExit();
    return 0; 
}
