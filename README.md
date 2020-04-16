# internet-status-reporter

Since it seems inevitable that an ISP will suck at giving a reliable connection, I've decided to build this app to report all the internet outtages that occur.

### Setup
1. Clone the repo onto a machine that will be running for the marjority of the time (I used an old Raspberry Pi for this)
2. Get Python3.6+ installed along with `pip`
3. Install the required modules with `python3 -m pip install -r requirements.txt`
4. Setup a MySQL database somewhere, and the `outtages` table with the following SQL:
  ```
   CREATE TABLE `outtages` (
     `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
     `loss` float NOT NULLDEFAULT 0.0,
     `downtime` varchar(255) NOT NULL,
     `created_at` datetime DEFAULT NULL
   );
 ```
5. Copy the `.env.sample` to make your `.env` file with all the appropriate credentials to connect to the database
6. Setup a cronjob to run the script, with `crontab -e` and append the following lines to the end of the file:
  ```
   #This runs the app every minute. It is possible that this could miss some outtages if the app runs too quickly
   */1 * * * * cd <path_to_repo>/internet-status-reporter/ && python3 app.py
   
   #Note that this will delete the log file once a day at midnight, to avoid taking up too much memory on the machine
   0 0 */1 * * rm <path_to_repo>/internet-status-reporter/log.txt
  ```



### Helpful Queries
#### Setting up the Table
```
 CREATE TABLE `outtages` (
   `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
   `loss` float NOT NULLDEFAULT 0.0,
   `downtime` varchar(255) NOT NULL,
   `created_at` datetime DEFAULT NULL
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
