# internet-status-reporter

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/db9ca02c405e41b0be621f3c68643e14)](https://app.codacy.com/manual/erunks/internet-status-reporter?utm_source=github.com&utm_medium=referral&utm_content=erunks/internet-status-reporter&utm_campaign=Badge_Grade_Dashboard)

Since it seems inevitable that an ISP will suck at giving a reliable connection, I've decided to build this app to report all the internet outtages that occur.

### Setup
1. Clone the repo onto a machine that will be running for the marjority of the time (I used an old Raspberry Pi for this)
2. Get Python3.6+ installed along with `pip`
3. Install the required modules with `python3 -m pip install -r requirements.txt`
4. Setup a MySQL database somewhere, and the `outtages` table with the following SQL:
  ```
   CREATE TABLE `outtages` (
     `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
     `loss` float NOT NULL DEFAULT '0',
     `downtime` varchar(255) NOT NULL,
     `created_at` datetime DEFAULT NULL,
     `maintenance` tinyint(1) NOT NULL DEFAULT '0',
     `info` text NOT NULL
   );
 ```
5. Copy the `.env.sample` to make your `.env` file with all the appropriate credentials to connect to the database
6. Setup a cronjob to run the script, with `crontab -e` and append the following lines to the end of the file:
  ```
   # This runs the app every minute. It is possible that this could miss some outtages if the app runs too quickly
   */1 * * * * cd <path_to_repo>/internet-status-reporter/ && flock -n /tmp/ISR.lck python3 app.py
      
   # Note the `flock -n /tmp/ISR.lck` part of the cronjob abvoe makes it so that only one instance of the program is 
   # allowed to be run at a time. This is optional, but does provide more accurate reporting. If you decide to add 
   # this in, make sure that you create the `/tmp/ISR.lck` file with a `touch`. 

   
   # This will delete the log file once a day at midnight, to avoid taking up too much memory on the machine
   0 0 */1 * * rm <path_to_repo>/internet-status-reporter/log.txt


   # This will help keep the app running the most updated version, so you don't have to manage updates by yourself
   0 0 * * 1 cd <path_to_repo>/internet-status-reporter/ && sh scripts/update.sh
  ```


### Helpful Queries
#### Setting up the Table
```
 CREATE TABLE `outtages` (
   `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
   `loss` float NOT NULL DEFAULT '0',
   `downtime` varchar(255) NOT NULL,
   `created_at` datetime DEFAULT NULL,
   `maintenance` tinyint(1) NOT NULL DEFAULT '0',
   `info` text NOT NULL
 );
```

#### Get Daily Statistics
```
select
count(`downtime`) as 'Number of Outtages',
sum(cast(`downtime` as time))/60 as 'Downtime in Minutes',
(sum(cast(`downtime` as time))/60)/count(`downtime`) as 'Average Downtime in Minutes',
max(cast(`downtime` as time)) as 'Longest Outtage',
cast(`created_at` as date) as 'Date'
from 
`outtages`
group by
cast(`created_at` as date)
;
```
