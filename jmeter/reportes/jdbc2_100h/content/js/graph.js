/*
   Licensed to the Apache Software Foundation (ASF) under one or more
   contributor license agreements.  See the NOTICE file distributed with
   this work for additional information regarding copyright ownership.
   The ASF licenses this file to You under the Apache License, Version 2.0
   (the "License"); you may not use this file except in compliance with
   the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/
$(document).ready(function() {

    $(".click-title").mouseenter( function(    e){
        e.preventDefault();
        this.style.cursor="pointer";
    });
    $(".click-title").mousedown( function(event){
        event.preventDefault();
    });

    // Ugly code while this script is shared among several pages
    try{
        refreshHitsPerSecond(true);
    } catch(e){}
    try{
        refreshResponseTimeOverTime(true);
    } catch(e){}
    try{
        refreshResponseTimePercentiles();
    } catch(e){}
});


var responseTimePercentilesInfos = {
        data: {"result": {"minY": 12.0, "minX": 0.0, "maxY": 9363.0, "series": [{"data": [[0.0, 12.0], [0.1, 16.0], [0.2, 20.0], [0.3, 21.0], [0.4, 21.0], [0.5, 22.0], [0.6, 22.0], [0.7, 22.0], [0.8, 22.0], [0.9, 22.0], [1.0, 22.0], [1.1, 22.0], [1.2, 22.0], [1.3, 22.0], [1.4, 22.0], [1.5, 22.0], [1.6, 22.0], [1.7, 23.0], [1.8, 23.0], [1.9, 23.0], [2.0, 23.0], [2.1, 23.0], [2.2, 23.0], [2.3, 23.0], [2.4, 23.0], [2.5, 23.0], [2.6, 23.0], [2.7, 23.0], [2.8, 23.0], [2.9, 23.0], [3.0, 23.0], [3.1, 24.0], [3.2, 24.0], [3.3, 24.0], [3.4, 24.0], [3.5, 24.0], [3.6, 24.0], [3.7, 24.0], [3.8, 24.0], [3.9, 24.0], [4.0, 25.0], [4.1, 25.0], [4.2, 25.0], [4.3, 25.0], [4.4, 25.0], [4.5, 25.0], [4.6, 25.0], [4.7, 25.0], [4.8, 25.0], [4.9, 25.0], [5.0, 26.0], [5.1, 26.0], [5.2, 26.0], [5.3, 26.0], [5.4, 26.0], [5.5, 26.0], [5.6, 27.0], [5.7, 27.0], [5.8, 27.0], [5.9, 27.0], [6.0, 28.0], [6.1, 28.0], [6.2, 28.0], [6.3, 28.0], [6.4, 29.0], [6.5, 29.0], [6.6, 29.0], [6.7, 29.0], [6.8, 30.0], [6.9, 30.0], [7.0, 31.0], [7.1, 31.0], [7.2, 32.0], [7.3, 32.0], [7.4, 33.0], [7.5, 34.0], [7.6, 34.0], [7.7, 35.0], [7.8, 35.0], [7.9, 36.0], [8.0, 37.0], [8.1, 38.0], [8.2, 39.0], [8.3, 39.0], [8.4, 41.0], [8.5, 42.0], [8.6, 43.0], [8.7, 44.0], [8.8, 46.0], [8.9, 46.0], [9.0, 47.0], [9.1, 49.0], [9.2, 50.0], [9.3, 50.0], [9.4, 52.0], [9.5, 53.0], [9.6, 55.0], [9.7, 55.0], [9.8, 56.0], [9.9, 57.0], [10.0, 57.0], [10.1, 58.0], [10.2, 59.0], [10.3, 60.0], [10.4, 60.0], [10.5, 61.0], [10.6, 61.0], [10.7, 62.0], [10.8, 62.0], [10.9, 63.0], [11.0, 64.0], [11.1, 64.0], [11.2, 65.0], [11.3, 65.0], [11.4, 66.0], [11.5, 67.0], [11.6, 67.0], [11.7, 68.0], [11.8, 69.0], [11.9, 69.0], [12.0, 70.0], [12.1, 70.0], [12.2, 71.0], [12.3, 71.0], [12.4, 72.0], [12.5, 73.0], [12.6, 73.0], [12.7, 75.0], [12.8, 75.0], [12.9, 76.0], [13.0, 77.0], [13.1, 78.0], [13.2, 79.0], [13.3, 80.0], [13.4, 82.0], [13.5, 82.0], [13.6, 83.0], [13.7, 85.0], [13.8, 86.0], [13.9, 87.0], [14.0, 88.0], [14.1, 89.0], [14.2, 90.0], [14.3, 91.0], [14.4, 94.0], [14.5, 95.0], [14.6, 97.0], [14.7, 98.0], [14.8, 99.0], [14.9, 101.0], [15.0, 102.0], [15.1, 104.0], [15.2, 106.0], [15.3, 108.0], [15.4, 111.0], [15.5, 112.0], [15.6, 115.0], [15.7, 119.0], [15.8, 120.0], [15.9, 123.0], [16.0, 125.0], [16.1, 129.0], [16.2, 130.0], [16.3, 131.0], [16.4, 132.0], [16.5, 133.0], [16.6, 134.0], [16.7, 134.0], [16.8, 135.0], [16.9, 136.0], [17.0, 136.0], [17.1, 136.0], [17.2, 137.0], [17.3, 137.0], [17.4, 137.0], [17.5, 138.0], [17.6, 138.0], [17.7, 138.0], [17.8, 139.0], [17.9, 139.0], [18.0, 139.0], [18.1, 139.0], [18.2, 140.0], [18.3, 140.0], [18.4, 140.0], [18.5, 140.0], [18.6, 140.0], [18.7, 140.0], [18.8, 141.0], [18.9, 141.0], [19.0, 141.0], [19.1, 141.0], [19.2, 141.0], [19.3, 141.0], [19.4, 142.0], [19.5, 142.0], [19.6, 142.0], [19.7, 142.0], [19.8, 142.0], [19.9, 142.0], [20.0, 143.0], [20.1, 143.0], [20.2, 143.0], [20.3, 143.0], [20.4, 143.0], [20.5, 143.0], [20.6, 143.0], [20.7, 144.0], [20.8, 144.0], [20.9, 144.0], [21.0, 144.0], [21.1, 144.0], [21.2, 144.0], [21.3, 144.0], [21.4, 144.0], [21.5, 145.0], [21.6, 145.0], [21.7, 145.0], [21.8, 145.0], [21.9, 145.0], [22.0, 145.0], [22.1, 145.0], [22.2, 145.0], [22.3, 145.0], [22.4, 145.0], [22.5, 145.0], [22.6, 145.0], [22.7, 146.0], [22.8, 146.0], [22.9, 146.0], [23.0, 146.0], [23.1, 146.0], [23.2, 146.0], [23.3, 146.0], [23.4, 146.0], [23.5, 146.0], [23.6, 146.0], [23.7, 147.0], [23.8, 147.0], [23.9, 147.0], [24.0, 147.0], [24.1, 147.0], [24.2, 147.0], [24.3, 147.0], [24.4, 147.0], [24.5, 147.0], [24.6, 147.0], [24.7, 147.0], [24.8, 148.0], [24.9, 148.0], [25.0, 148.0], [25.1, 148.0], [25.2, 148.0], [25.3, 148.0], [25.4, 148.0], [25.5, 148.0], [25.6, 148.0], [25.7, 148.0], [25.8, 148.0], [25.9, 148.0], [26.0, 148.0], [26.1, 149.0], [26.2, 149.0], [26.3, 149.0], [26.4, 149.0], [26.5, 149.0], [26.6, 149.0], [26.7, 149.0], [26.8, 149.0], [26.9, 149.0], [27.0, 149.0], [27.1, 149.0], [27.2, 149.0], [27.3, 149.0], [27.4, 150.0], [27.5, 150.0], [27.6, 150.0], [27.7, 150.0], [27.8, 150.0], [27.9, 150.0], [28.0, 150.0], [28.1, 150.0], [28.2, 150.0], [28.3, 150.0], [28.4, 150.0], [28.5, 150.0], [28.6, 150.0], [28.7, 150.0], [28.8, 150.0], [28.9, 151.0], [29.0, 151.0], [29.1, 151.0], [29.2, 151.0], [29.3, 151.0], [29.4, 151.0], [29.5, 151.0], [29.6, 151.0], [29.7, 151.0], [29.8, 151.0], [29.9, 151.0], [30.0, 151.0], [30.1, 151.0], [30.2, 151.0], [30.3, 151.0], [30.4, 151.0], [30.5, 152.0], [30.6, 152.0], [30.7, 152.0], [30.8, 152.0], [30.9, 152.0], [31.0, 152.0], [31.1, 152.0], [31.2, 152.0], [31.3, 152.0], [31.4, 152.0], [31.5, 152.0], [31.6, 152.0], [31.7, 152.0], [31.8, 152.0], [31.9, 152.0], [32.0, 152.0], [32.1, 153.0], [32.2, 153.0], [32.3, 153.0], [32.4, 153.0], [32.5, 153.0], [32.6, 153.0], [32.7, 153.0], [32.8, 153.0], [32.9, 153.0], [33.0, 153.0], [33.1, 153.0], [33.2, 153.0], [33.3, 153.0], [33.4, 153.0], [33.5, 153.0], [33.6, 153.0], [33.7, 153.0], [33.8, 153.0], [33.9, 154.0], [34.0, 154.0], [34.1, 154.0], [34.2, 154.0], [34.3, 154.0], [34.4, 154.0], [34.5, 154.0], [34.6, 154.0], [34.7, 154.0], [34.8, 154.0], [34.9, 154.0], [35.0, 154.0], [35.1, 154.0], [35.2, 154.0], [35.3, 154.0], [35.4, 155.0], [35.5, 155.0], [35.6, 155.0], [35.7, 155.0], [35.8, 155.0], [35.9, 155.0], [36.0, 155.0], [36.1, 155.0], [36.2, 155.0], [36.3, 155.0], [36.4, 155.0], [36.5, 155.0], [36.6, 155.0], [36.7, 155.0], [36.8, 155.0], [36.9, 155.0], [37.0, 156.0], [37.1, 156.0], [37.2, 156.0], [37.3, 156.0], [37.4, 156.0], [37.5, 156.0], [37.6, 156.0], [37.7, 156.0], [37.8, 156.0], [37.9, 156.0], [38.0, 156.0], [38.1, 156.0], [38.2, 156.0], [38.3, 156.0], [38.4, 156.0], [38.5, 156.0], [38.6, 156.0], [38.7, 157.0], [38.8, 157.0], [38.9, 157.0], [39.0, 157.0], [39.1, 157.0], [39.2, 157.0], [39.3, 157.0], [39.4, 157.0], [39.5, 157.0], [39.6, 157.0], [39.7, 157.0], [39.8, 157.0], [39.9, 157.0], [40.0, 157.0], [40.1, 157.0], [40.2, 157.0], [40.3, 157.0], [40.4, 157.0], [40.5, 157.0], [40.6, 158.0], [40.7, 158.0], [40.8, 158.0], [40.9, 158.0], [41.0, 158.0], [41.1, 158.0], [41.2, 158.0], [41.3, 158.0], [41.4, 158.0], [41.5, 158.0], [41.6, 158.0], [41.7, 158.0], [41.8, 158.0], [41.9, 158.0], [42.0, 158.0], [42.1, 158.0], [42.2, 158.0], [42.3, 159.0], [42.4, 159.0], [42.5, 159.0], [42.6, 159.0], [42.7, 159.0], [42.8, 159.0], [42.9, 159.0], [43.0, 159.0], [43.1, 159.0], [43.2, 159.0], [43.3, 159.0], [43.4, 159.0], [43.5, 159.0], [43.6, 159.0], [43.7, 159.0], [43.8, 159.0], [43.9, 160.0], [44.0, 160.0], [44.1, 160.0], [44.2, 160.0], [44.3, 160.0], [44.4, 160.0], [44.5, 160.0], [44.6, 160.0], [44.7, 160.0], [44.8, 160.0], [44.9, 160.0], [45.0, 160.0], [45.1, 160.0], [45.2, 160.0], [45.3, 160.0], [45.4, 160.0], [45.5, 160.0], [45.6, 161.0], [45.7, 161.0], [45.8, 161.0], [45.9, 161.0], [46.0, 161.0], [46.1, 161.0], [46.2, 161.0], [46.3, 161.0], [46.4, 161.0], [46.5, 161.0], [46.6, 161.0], [46.7, 161.0], [46.8, 161.0], [46.9, 161.0], [47.0, 162.0], [47.1, 162.0], [47.2, 162.0], [47.3, 162.0], [47.4, 162.0], [47.5, 162.0], [47.6, 162.0], [47.7, 162.0], [47.8, 162.0], [47.9, 162.0], [48.0, 162.0], [48.1, 162.0], [48.2, 162.0], [48.3, 162.0], [48.4, 162.0], [48.5, 162.0], [48.6, 163.0], [48.7, 163.0], [48.8, 163.0], [48.9, 163.0], [49.0, 163.0], [49.1, 163.0], [49.2, 163.0], [49.3, 163.0], [49.4, 163.0], [49.5, 163.0], [49.6, 163.0], [49.7, 163.0], [49.8, 163.0], [49.9, 164.0], [50.0, 164.0], [50.1, 164.0], [50.2, 164.0], [50.3, 164.0], [50.4, 164.0], [50.5, 164.0], [50.6, 164.0], [50.7, 164.0], [50.8, 164.0], [50.9, 164.0], [51.0, 164.0], [51.1, 164.0], [51.2, 164.0], [51.3, 165.0], [51.4, 165.0], [51.5, 165.0], [51.6, 165.0], [51.7, 165.0], [51.8, 165.0], [51.9, 165.0], [52.0, 165.0], [52.1, 165.0], [52.2, 165.0], [52.3, 165.0], [52.4, 165.0], [52.5, 165.0], [52.6, 166.0], [52.7, 166.0], [52.8, 166.0], [52.9, 166.0], [53.0, 166.0], [53.1, 166.0], [53.2, 166.0], [53.3, 166.0], [53.4, 166.0], [53.5, 166.0], [53.6, 166.0], [53.7, 166.0], [53.8, 166.0], [53.9, 167.0], [54.0, 167.0], [54.1, 167.0], [54.2, 167.0], [54.3, 167.0], [54.4, 167.0], [54.5, 167.0], [54.6, 167.0], [54.7, 167.0], [54.8, 167.0], [54.9, 167.0], [55.0, 167.0], [55.1, 167.0], [55.2, 167.0], [55.3, 168.0], [55.4, 168.0], [55.5, 168.0], [55.6, 168.0], [55.7, 168.0], [55.8, 168.0], [55.9, 168.0], [56.0, 168.0], [56.1, 168.0], [56.2, 168.0], [56.3, 168.0], [56.4, 169.0], [56.5, 169.0], [56.6, 169.0], [56.7, 169.0], [56.8, 169.0], [56.9, 169.0], [57.0, 169.0], [57.1, 169.0], [57.2, 169.0], [57.3, 169.0], [57.4, 170.0], [57.5, 170.0], [57.6, 170.0], [57.7, 170.0], [57.8, 170.0], [57.9, 170.0], [58.0, 170.0], [58.1, 170.0], [58.2, 170.0], [58.3, 170.0], [58.4, 171.0], [58.5, 171.0], [58.6, 171.0], [58.7, 171.0], [58.8, 171.0], [58.9, 171.0], [59.0, 171.0], [59.1, 171.0], [59.2, 171.0], [59.3, 171.0], [59.4, 171.0], [59.5, 172.0], [59.6, 172.0], [59.7, 172.0], [59.8, 172.0], [59.9, 172.0], [60.0, 172.0], [60.1, 172.0], [60.2, 172.0], [60.3, 172.0], [60.4, 172.0], [60.5, 173.0], [60.6, 173.0], [60.7, 173.0], [60.8, 173.0], [60.9, 173.0], [61.0, 173.0], [61.1, 173.0], [61.2, 173.0], [61.3, 173.0], [61.4, 174.0], [61.5, 174.0], [61.6, 174.0], [61.7, 174.0], [61.8, 174.0], [61.9, 174.0], [62.0, 174.0], [62.1, 174.0], [62.2, 175.0], [62.3, 175.0], [62.4, 175.0], [62.5, 175.0], [62.6, 175.0], [62.7, 175.0], [62.8, 175.0], [62.9, 175.0], [63.0, 176.0], [63.1, 176.0], [63.2, 176.0], [63.3, 176.0], [63.4, 176.0], [63.5, 176.0], [63.6, 177.0], [63.7, 177.0], [63.8, 177.0], [63.9, 177.0], [64.0, 177.0], [64.1, 177.0], [64.2, 177.0], [64.3, 177.0], [64.4, 178.0], [64.5, 178.0], [64.6, 178.0], [64.7, 178.0], [64.8, 178.0], [64.9, 178.0], [65.0, 178.0], [65.1, 178.0], [65.2, 179.0], [65.3, 179.0], [65.4, 179.0], [65.5, 179.0], [65.6, 179.0], [65.7, 180.0], [65.8, 180.0], [65.9, 180.0], [66.0, 180.0], [66.1, 180.0], [66.2, 180.0], [66.3, 180.0], [66.4, 181.0], [66.5, 181.0], [66.6, 181.0], [66.7, 181.0], [66.8, 181.0], [66.9, 182.0], [67.0, 182.0], [67.1, 182.0], [67.2, 182.0], [67.3, 182.0], [67.4, 183.0], [67.5, 183.0], [67.6, 183.0], [67.7, 183.0], [67.8, 183.0], [67.9, 184.0], [68.0, 184.0], [68.1, 184.0], [68.2, 184.0], [68.3, 185.0], [68.4, 185.0], [68.5, 186.0], [68.6, 186.0], [68.7, 186.0], [68.8, 186.0], [68.9, 187.0], [69.0, 187.0], [69.1, 187.0], [69.2, 188.0], [69.3, 188.0], [69.4, 188.0], [69.5, 189.0], [69.6, 189.0], [69.7, 190.0], [69.8, 190.0], [69.9, 191.0], [70.0, 191.0], [70.1, 191.0], [70.2, 192.0], [70.3, 192.0], [70.4, 193.0], [70.5, 193.0], [70.6, 193.0], [70.7, 194.0], [70.8, 194.0], [70.9, 195.0], [71.0, 196.0], [71.1, 197.0], [71.2, 198.0], [71.3, 199.0], [71.4, 202.0], [71.5, 204.0], [71.6, 207.0], [71.7, 210.0], [71.8, 214.0], [71.9, 216.0], [72.0, 219.0], [72.1, 224.0], [72.2, 230.0], [72.3, 239.0], [72.4, 245.0], [72.5, 252.0], [72.6, 259.0], [72.7, 269.0], [72.8, 278.0], [72.9, 292.0], [73.0, 303.0], [73.1, 318.0], [73.2, 333.0], [73.3, 349.0], [73.4, 358.0], [73.5, 363.0], [73.6, 369.0], [73.7, 373.0], [73.8, 379.0], [73.9, 385.0], [74.0, 400.0], [74.1, 412.0], [74.2, 420.0], [74.3, 439.0], [74.4, 472.0], [74.5, 480.0], [74.6, 484.0], [74.7, 488.0], [74.8, 491.0], [74.9, 493.0], [75.0, 495.0], [75.1, 497.0], [75.2, 500.0], [75.3, 502.0], [75.4, 504.0], [75.5, 505.0], [75.6, 507.0], [75.7, 507.0], [75.8, 510.0], [75.9, 511.0], [76.0, 512.0], [76.1, 513.0], [76.2, 515.0], [76.3, 515.0], [76.4, 517.0], [76.5, 517.0], [76.6, 518.0], [76.7, 519.0], [76.8, 520.0], [76.9, 521.0], [77.0, 521.0], [77.1, 522.0], [77.2, 523.0], [77.3, 524.0], [77.4, 525.0], [77.5, 526.0], [77.6, 527.0], [77.7, 527.0], [77.8, 528.0], [77.9, 529.0], [78.0, 530.0], [78.1, 530.0], [78.2, 531.0], [78.3, 531.0], [78.4, 532.0], [78.5, 533.0], [78.6, 533.0], [78.7, 534.0], [78.8, 535.0], [78.9, 535.0], [79.0, 537.0], [79.1, 538.0], [79.2, 539.0], [79.3, 540.0], [79.4, 541.0], [79.5, 542.0], [79.6, 542.0], [79.7, 543.0], [79.8, 544.0], [79.9, 544.0], [80.0, 545.0], [80.1, 546.0], [80.2, 547.0], [80.3, 548.0], [80.4, 548.0], [80.5, 549.0], [80.6, 550.0], [80.7, 551.0], [80.8, 552.0], [80.9, 553.0], [81.0, 554.0], [81.1, 555.0], [81.2, 555.0], [81.3, 556.0], [81.4, 558.0], [81.5, 559.0], [81.6, 559.0], [81.7, 560.0], [81.8, 561.0], [81.9, 562.0], [82.0, 563.0], [82.1, 564.0], [82.2, 566.0], [82.3, 567.0], [82.4, 568.0], [82.5, 570.0], [82.6, 572.0], [82.7, 574.0], [82.8, 576.0], [82.9, 578.0], [83.0, 580.0], [83.1, 581.0], [83.2, 583.0], [83.3, 585.0], [83.4, 587.0], [83.5, 590.0], [83.6, 591.0], [83.7, 594.0], [83.8, 596.0], [83.9, 600.0], [84.0, 605.0], [84.1, 614.0], [84.2, 635.0], [84.3, 676.0], [84.4, 752.0], [84.5, 812.0], [84.6, 836.0], [84.7, 846.0], [84.8, 854.0], [84.9, 862.0], [85.0, 866.0], [85.1, 868.0], [85.2, 873.0], [85.3, 878.0], [85.4, 882.0], [85.5, 884.0], [85.6, 888.0], [85.7, 890.0], [85.8, 892.0], [85.9, 895.0], [86.0, 897.0], [86.1, 899.0], [86.2, 901.0], [86.3, 902.0], [86.4, 903.0], [86.5, 905.0], [86.6, 908.0], [86.7, 911.0], [86.8, 914.0], [86.9, 916.0], [87.0, 919.0], [87.1, 922.0], [87.2, 924.0], [87.3, 926.0], [87.4, 927.0], [87.5, 929.0], [87.6, 932.0], [87.7, 935.0], [87.8, 938.0], [87.9, 942.0], [88.0, 943.0], [88.1, 945.0], [88.2, 947.0], [88.3, 949.0], [88.4, 951.0], [88.5, 955.0], [88.6, 959.0], [88.7, 969.0], [88.8, 974.0], [88.9, 981.0], [89.0, 1002.0], [89.1, 1096.0], [89.2, 1159.0], [89.3, 1200.0], [89.4, 1214.0], [89.5, 1224.0], [89.6, 1232.0], [89.7, 1241.0], [89.8, 1248.0], [89.9, 1254.0], [90.0, 1261.0], [90.1, 1265.0], [90.2, 1268.0], [90.3, 1271.0], [90.4, 1276.0], [90.5, 1282.0], [90.6, 1287.0], [90.7, 1289.0], [90.8, 1292.0], [90.9, 1298.0], [91.0, 1301.0], [91.1, 1304.0], [91.2, 1308.0], [91.3, 1310.0], [91.4, 1314.0], [91.5, 1317.0], [91.6, 1321.0], [91.7, 1327.0], [91.8, 1332.0], [91.9, 1336.0], [92.0, 1342.0], [92.1, 1346.0], [92.2, 1352.0], [92.3, 1366.0], [92.4, 1395.0], [92.5, 1541.0], [92.6, 1568.0], [92.7, 1586.0], [92.8, 1600.0], [92.9, 1623.0], [93.0, 1631.0], [93.1, 1636.0], [93.2, 1644.0], [93.3, 1650.0], [93.4, 1655.0], [93.5, 1663.0], [93.6, 1670.0], [93.7, 1674.0], [93.8, 1679.0], [93.9, 1690.0], [94.0, 1703.0], [94.1, 1714.0], [94.2, 1720.0], [94.3, 1727.0], [94.4, 1738.0], [94.5, 1756.0], [94.6, 1928.0], [94.7, 1953.0], [94.8, 1974.0], [94.9, 2009.0], [95.0, 2022.0], [95.1, 2034.0], [95.2, 2039.0], [95.3, 2048.0], [95.4, 2055.0], [95.5, 2059.0], [95.6, 2066.0], [95.7, 2077.0], [95.8, 2091.0], [95.9, 2107.0], [96.0, 2127.0], [96.1, 2263.0], [96.2, 2312.0], [96.3, 2359.0], [96.4, 2384.0], [96.5, 2394.0], [96.6, 2417.0], [96.7, 2426.0], [96.8, 2444.0], [96.9, 2461.0], [97.0, 2480.0], [97.1, 2507.0], [97.2, 2678.0], [97.3, 2746.0], [97.4, 2784.0], [97.5, 2807.0], [97.6, 2827.0], [97.7, 2848.0], [97.8, 2874.0], [97.9, 3047.0], [98.0, 3106.0], [98.1, 3142.0], [98.2, 3203.0], [98.3, 3239.0], [98.4, 3402.0], [98.5, 3499.0], [98.6, 3569.0], [98.7, 3612.0], [98.8, 3817.0], [98.9, 3904.0], [99.0, 4021.0], [99.1, 4248.0], [99.2, 4331.0], [99.3, 4468.0], [99.4, 4571.0], [99.5, 4898.0], [99.6, 5132.0], [99.7, 5618.0], [99.8, 6541.0], [99.9, 6951.0], [100.0, 9363.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 100.0, "title": "Response Time Percentiles"}},
        getOptions: function() {
            return {
                series: {
                    points: { show: false }
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentiles'
                },
                xaxis: {
                    tickDecimals: 1,
                    axisLabel: "Percentiles",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Percentile value in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : %x.2 percentile was %y ms"
                },
                selection: { mode: "xy" },
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentiles"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesPercentiles"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesPercentiles"), dataset, prepareOverviewOptions(options));
        }
};

/**
 * @param elementId Id of element where we display message
 */
function setEmptyGraph(elementId) {
    $(function() {
        $(elementId).text("No graph series with filter="+seriesFilter);
    });
}

// Response times percentiles
function refreshResponseTimePercentiles() {
    var infos = responseTimePercentilesInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimePercentiles");
        return;
    }
    if (isGraph($("#flotResponseTimesPercentiles"))){
        infos.createGraph();
    } else {
        var choiceContainer = $("#choicesResponseTimePercentiles");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesPercentiles", "#overviewResponseTimesPercentiles");
        $('#bodyResponseTimePercentiles .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimeDistributionInfos = {
        data: {"result": {"minY": 1.0, "minX": 0.0, "maxY": 5056.0, "series": [{"data": [[0.0, 1327.0], [600.0, 40.0], [700.0, 12.0], [800.0, 149.0], [900.0, 257.0], [1000.0, 10.0], [1100.0, 17.0], [1200.0, 148.0], [1300.0, 131.0], [1400.0, 3.0], [1500.0, 31.0], [1600.0, 107.0], [1700.0, 50.0], [1800.0, 1.0], [1900.0, 29.0], [2000.0, 87.0], [2100.0, 20.0], [2300.0, 34.0], [2200.0, 6.0], [2400.0, 50.0], [2500.0, 5.0], [2600.0, 8.0], [2700.0, 19.0], [2800.0, 37.0], [3000.0, 9.0], [3100.0, 21.0], [3200.0, 16.0], [3300.0, 2.0], [3400.0, 10.0], [3500.0, 15.0], [3600.0, 7.0], [3700.0, 2.0], [3800.0, 11.0], [3900.0, 9.0], [4000.0, 1.0], [4300.0, 12.0], [4200.0, 10.0], [4100.0, 4.0], [4600.0, 4.0], [4500.0, 8.0], [4400.0, 4.0], [4700.0, 1.0], [4800.0, 2.0], [5100.0, 1.0], [5000.0, 4.0], [4900.0, 4.0], [5200.0, 2.0], [5400.0, 3.0], [5500.0, 2.0], [5600.0, 3.0], [5700.0, 2.0], [5900.0, 4.0], [6000.0, 1.0], [6500.0, 2.0], [6600.0, 4.0], [6900.0, 1.0], [6700.0, 3.0], [7400.0, 1.0], [7600.0, 2.0], [8500.0, 1.0], [8700.0, 1.0], [8600.0, 2.0], [9300.0, 1.0], [100.0, 5056.0], [200.0, 149.0], [300.0, 91.0], [400.0, 104.0], [500.0, 780.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 100, "maxX": 9300.0, "title": "Response Time Distribution"}},
        getOptions: function() {
            var granularity = this.data.result.granularity;
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    barWidth: this.data.result.granularity
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " responses for " + label + " were between " + xval + " and " + (xval + granularity) + " ms";
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimeDistribution"), prepareData(data.result.series, $("#choicesResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshResponseTimeDistribution() {
    var infos = responseTimeDistributionInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeDistribution");
        return;
    }
    if (isGraph($("#flotResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var syntheticResponseTimeDistributionInfos = {
        data: {"result": {"minY": 676.0, "minX": 0.0, "ticks": [[0, "Requests having \nresponse time <= 500ms"], [1, "Requests having \nresponse time > 500ms and <= 1,500ms"], [2, "Requests having \nresponse time > 1,500ms"], [3, "Requests in error"]], "maxY": 6732.0, "series": [{"data": [[0.0, 6732.0]], "color": "#9ACD32", "isOverall": false, "label": "Requests having \nresponse time <= 500ms", "isController": false}, {"data": [[1.0, 1542.0]], "color": "yellow", "isOverall": false, "label": "Requests having \nresponse time > 500ms and <= 1,500ms", "isController": false}, {"data": [[2.0, 676.0]], "color": "orange", "isOverall": false, "label": "Requests having \nresponse time > 1,500ms", "isController": false}, {"data": [], "color": "#FF6347", "isOverall": false, "label": "Requests in error", "isController": false}], "supportsControllersDiscrimination": false, "maxX": 2.0, "title": "Synthetic Response Times Distribution"}},
        getOptions: function() {
            return {
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendSyntheticResponseTimeDistribution'
                },
                xaxis:{
                    axisLabel: "Response times ranges",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                    tickLength:0,
                    min:-0.5,
                    max:3.5
                },
                yaxis: {
                    axisLabel: "Number of responses",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                bars : {
                    show: true,
                    align: "center",
                    barWidth: 0.25,
                    fill:.75
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: function(label, xval, yval, flotItem){
                        return yval + " " + label;
                    }
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var options = this.getOptions();
            prepareOptions(options, data);
            options.xaxis.ticks = data.result.ticks;
            $.plot($("#flotSyntheticResponseTimeDistribution"), prepareData(data.result.series, $("#choicesSyntheticResponseTimeDistribution")), options);
        }

};

// Response time distribution
function refreshSyntheticResponseTimeDistribution() {
    var infos = syntheticResponseTimeDistributionInfos;
    prepareSeries(infos.data, true);
    if (isGraph($("#flotSyntheticResponseTimeDistribution"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        $('#footerSyntheticResponseTimeDistribution .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var activeThreadsOverTimeInfos = {
        data: {"result": {"minY": 47.1798780487804, "minX": 1.79493684E12, "maxY": 97.48071135430897, "series": [{"data": [[1.79493684E12, 47.1798780487804], [1.7949369E12, 97.48071135430897]], "isOverall": false, "label": "Hilos JDBC", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.7949369E12, "title": "Active Threads Over Time"}},
        getOptions: function() {
            return {
                series: {
                    stack: true,
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 6,
                    show: true,
                    container: '#legendActiveThreadsOverTime'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                selection: {
                    mode: 'xy'
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : At %x there were %y active threads"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesActiveThreadsOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotActiveThreadsOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewActiveThreadsOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Active Threads Over Time
function refreshActiveThreadsOverTime(fixTimestamps) {
    var infos = activeThreadsOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotActiveThreadsOverTime"))) {
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesActiveThreadsOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotActiveThreadsOverTime", "#overviewActiveThreadsOverTime");
        $('#footerActiveThreadsOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var timeVsThreadsInfos = {
        data: {"result": {"minY": 52.26388888888888, "minX": 1.0, "maxY": 4571.0, "series": [{"data": [[2.0, 468.0], [4.0, 1196.0], [5.0, 480.0], [6.0, 1977.0], [7.0, 1241.0], [8.0, 492.0], [9.0, 3885.0], [10.0, 497.0], [11.0, 473.0], [12.0, 2018.0], [14.0, 1078.5], [15.0, 523.0], [16.0, 851.0], [17.0, 4571.0], [18.0, 516.0], [19.0, 506.0], [20.0, 1252.0], [21.0, 495.0], [22.0, 530.0], [23.0, 1659.0], [26.0, 1830.3333333333333], [27.0, 895.0], [28.0, 1256.0], [29.0, 897.0], [30.0, 2462.0], [31.0, 555.0], [33.0, 2066.0], [32.0, 2444.0], [35.0, 841.6712328767122], [34.0, 2073.0], [36.0, 69.92537313432837], [37.0, 57.050000000000004], [38.0, 65.60869565217392], [39.0, 55.46268656716419], [40.0, 82.85000000000001], [41.0, 95.70833333333334], [42.0, 60.661290322580655], [43.0, 52.26388888888888], [44.0, 92.08955223880596], [45.0, 57.1159420289855], [46.0, 90.27692307692308], [47.0, 81.17543859649123], [48.0, 52.72463768115943], [49.0, 83.95522388059703], [50.0, 72.01587301587303], [51.0, 99.34920634920638], [52.0, 155.0], [53.0, 173.53731343283584], [54.0, 156.41935483870967], [55.0, 109.93220338983053], [56.0, 139.72881355932202], [57.0, 141.58490566037736], [58.0, 112.11111111111109], [59.0, 127.87755102040816], [60.0, 147.31372549019608], [61.0, 193.22222222222223], [62.0, 189.04000000000002], [63.0, 213.40740740740736], [64.0, 479.68749999999994], [65.0, 333.23809523809524], [66.0, 354.6666666666667], [67.0, 356.1875], [68.0, 321.5652173913044], [69.0, 329.5238095238096], [70.0, 353.5], [71.0, 286.45], [72.0, 634.6875], [73.0, 465.5999999999999], [74.0, 365.28571428571433], [75.0, 338.2222222222222], [76.0, 505.7058823529412], [77.0, 474.52941176470586], [78.0, 383.0], [79.0, 251.6153846153846], [80.0, 765.2222222222222], [81.0, 555.0625], [82.0, 340.3076923076923], [83.0, 357.71428571428567], [84.0, 435.70588235294116], [85.0, 628.8666666666667], [86.0, 875.25], [87.0, 702.4736842105262], [88.0, 635.0000000000001], [89.0, 449.33333333333337], [90.0, 464.44444444444446], [91.0, 379.05000000000007], [92.0, 414.3124999999999], [93.0, 540.5294117647059], [94.0, 502.4347826086958], [95.0, 401.35714285714283], [96.0, 559.6315789473684], [97.0, 605.3571428571429], [98.0, 606.2857142857143], [99.0, 466.529411764706], [100.0, 528.041552092882], [1.0, 1980.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}, {"data": [[88.26357541899402, 450.68983240223304]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)-Aggregated", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 100.0, "title": "Time VS Threads"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    axisLabel: "Number of active threads",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response times in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: { noColumns: 2,show: true, container: '#legendTimeVsThreads' },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s: At %x.2 active threads, Average response time was %y.2 ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesTimeVsThreads"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotTimesVsThreads"), dataset, options);
            // setup overview
            $.plot($("#overviewTimesVsThreads"), dataset, prepareOverviewOptions(options));
        }
};

// Time vs threads
function refreshTimeVsThreads(){
    var infos = timeVsThreadsInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTimeVsThreads");
        return;
    }
    if(isGraph($("#flotTimesVsThreads"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTimeVsThreads");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTimesVsThreads", "#overviewTimesVsThreads");
        $('#footerTimeVsThreads .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var bytesThroughputOverTimeInfos = {
        data : {"result": {"minY": 0.0, "minX": 1.79493684E12, "maxY": 119762.16666666667, "series": [{"data": [[1.79493684E12, 26868.666666666668], [1.7949369E12, 119762.16666666667]], "isOverall": false, "label": "Bytes received per second", "isController": false}, {"data": [[1.79493684E12, 0.0], [1.7949369E12, 0.0]], "isOverall": false, "label": "Bytes sent per second", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.7949369E12, "title": "Bytes Throughput Over Time"}},
        getOptions : function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity) ,
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Bytes / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendBytesThroughputOverTime'
                },
                selection: {
                    mode: "xy"
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y"
                }
            };
        },
        createGraph : function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesBytesThroughputOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotBytesThroughputOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewBytesThroughputOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Bytes throughput Over Time
function refreshBytesThroughputOverTime(fixTimestamps) {
    var infos = bytesThroughputOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotBytesThroughputOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesBytesThroughputOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotBytesThroughputOverTime", "#overviewBytesThroughputOverTime");
        $('#footerBytesThroughputOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var responseTimesOverTimeInfos = {
        data: {"result": {"minY": 110.03841463414633, "minX": 1.79493684E12, "maxY": 527.1150478796168, "series": [{"data": [[1.79493684E12, 110.03841463414633], [1.7949369E12, 527.1150478796168]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.7949369E12, "title": "Response Time Over Time"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average response time was %y ms"
                }
            };
        },
        createGraph: function() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Times Over Time
function refreshResponseTimeOverTime(fixTimestamps) {
    var infos = responseTimesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyResponseTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotResponseTimesOverTime"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimesOverTime", "#overviewResponseTimesOverTime");
        $('#footerResponseTimesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var latenciesOverTimeInfos = {
        data: {"result": {"minY": 109.14329268292678, "minX": 1.79493684E12, "maxY": 527.043228454174, "series": [{"data": [[1.79493684E12, 109.14329268292678], [1.7949369E12, 527.043228454174]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.7949369E12, "title": "Latencies Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average response latencies in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendLatenciesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average latency was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesLatenciesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotLatenciesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewLatenciesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Latencies Over Time
function refreshLatenciesOverTime(fixTimestamps) {
    var infos = latenciesOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyLatenciesOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotLatenciesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesLatenciesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotLatenciesOverTime", "#overviewLatenciesOverTime");
        $('#footerLatenciesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var connectTimeOverTimeInfos = {
        data: {"result": {"minY": 61.6676829268293, "minX": 1.79493684E12, "maxY": 365.1808481532155, "series": [{"data": [[1.79493684E12, 61.6676829268293], [1.7949369E12, 365.1808481532155]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.7949369E12, "title": "Connect Time Over Time"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getConnectTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Average Connect Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendConnectTimeOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Average connect time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesConnectTimeOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotConnectTimeOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewConnectTimeOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Connect Time Over Time
function refreshConnectTimeOverTime(fixTimestamps) {
    var infos = connectTimeOverTimeInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyConnectTimeOverTime");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotConnectTimeOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesConnectTimeOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotConnectTimeOverTime", "#overviewConnectTimeOverTime");
        $('#footerConnectTimeOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var responseTimePercentilesOverTimeInfos = {
        data: {"result": {"minY": 12.0, "minX": 1.79493684E12, "maxY": 9363.0, "series": [{"data": [[1.79493684E12, 3299.0], [1.7949369E12, 9363.0]], "isOverall": false, "label": "Max", "isController": false}, {"data": [[1.79493684E12, 12.0], [1.7949369E12, 16.0]], "isOverall": false, "label": "Min", "isController": false}, {"data": [[1.79493684E12, 163.0], [1.7949369E12, 1321.0]], "isOverall": false, "label": "90th percentile", "isController": false}, {"data": [[1.79493684E12, 1833.9999999999918], [1.7949369E12, 4327.89]], "isOverall": false, "label": "99th percentile", "isController": false}, {"data": [[1.79493684E12, 49.5], [1.7949369E12, 170.0]], "isOverall": false, "label": "Median", "isController": false}, {"data": [[1.79493684E12, 247.7499999999991], [1.7949369E12, 2083.8999999999996]], "isOverall": false, "label": "95th percentile", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.7949369E12, "title": "Response Time Percentiles Over Time (successful requests only)"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true,
                        fill: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Response Time in ms",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: '#legendResponseTimePercentilesOverTime'
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s : at %x Response time was %y ms"
                }
            };
        },
        createGraph: function () {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesResponseTimePercentilesOverTime"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotResponseTimePercentilesOverTime"), dataset, options);
            // setup overview
            $.plot($("#overviewResponseTimePercentilesOverTime"), dataset, prepareOverviewOptions(options));
        }
};

// Response Time Percentiles Over Time
function refreshResponseTimePercentilesOverTime(fixTimestamps) {
    var infos = responseTimePercentilesOverTimeInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotResponseTimePercentilesOverTime"))) {
        infos.createGraph();
    }else {
        var choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimePercentilesOverTime", "#overviewResponseTimePercentilesOverTime");
        $('#footerResponseTimePercentilesOverTime .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var responseTimeVsRequestInfos = {
    data: {"result": {"minY": 31.5, "minX": 94.0, "maxY": 892.0, "series": [{"data": [[547.0, 76.0], [651.0, 36.0], [94.0, 892.0], [158.0, 522.0], [166.0, 370.5], [164.0, 533.0], [180.0, 183.0], [179.0, 175.0], [183.0, 168.0], [181.0, 169.5], [182.0, 165.0], [176.0, 180.5], [187.0, 177.0], [184.0, 171.0], [188.0, 165.0], [189.0, 167.0], [185.0, 165.5], [186.0, 159.0], [191.0, 171.0], [190.0, 163.5], [198.0, 265.5], [192.0, 162.0], [196.0, 156.0], [194.0, 158.5], [200.0, 153.0], [442.0, 31.5]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 651.0, "title": "Response Time Vs Request"}},
    getOptions: function() {
        return {
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Response Time in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: {
                noColumns: 2,
                show: true,
                container: '#legendResponseTimeVsRequest'
            },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median response time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesResponseTimeVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotResponseTimeVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewResponseTimeVsRequest"), dataset, prepareOverviewOptions(options));

    }
};

// Response Time vs Request
function refreshResponseTimeVsRequest() {
    var infos = responseTimeVsRequestInfos;
    prepareSeries(infos.data);
    if (isGraph($("#flotResponseTimeVsRequest"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesResponseTimeVsRequest");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotResponseTimeVsRequest", "#overviewResponseTimeVsRequest");
        $('#footerResponseRimeVsRequest .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};


var latenciesVsRequestInfos = {
    data: {"result": {"minY": 31.0, "minX": 94.0, "maxY": 892.0, "series": [{"data": [[547.0, 76.0], [651.0, 35.0], [94.0, 892.0], [158.0, 522.0], [166.0, 370.5], [164.0, 533.0], [180.0, 183.0], [179.0, 175.0], [183.0, 168.0], [181.0, 169.5], [182.0, 165.0], [176.0, 180.5], [187.0, 177.0], [184.0, 171.0], [188.0, 165.0], [189.0, 167.0], [185.0, 165.5], [186.0, 159.0], [191.0, 171.0], [190.0, 163.5], [198.0, 265.5], [192.0, 162.0], [196.0, 156.0], [194.0, 158.5], [200.0, 153.0], [442.0, 31.0]], "isOverall": false, "label": "Successes", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 651.0, "title": "Latencies Vs Request"}},
    getOptions: function() {
        return{
            series: {
                lines: {
                    show: false
                },
                points: {
                    show: true
                }
            },
            xaxis: {
                axisLabel: "Global number of requests per second",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            yaxis: {
                axisLabel: "Median Latency in ms",
                axisLabelUseCanvas: true,
                axisLabelFontSizePixels: 12,
                axisLabelFontFamily: 'Verdana, Arial',
                axisLabelPadding: 20,
            },
            legend: { noColumns: 2,show: true, container: '#legendLatencyVsRequest' },
            selection: {
                mode: 'xy'
            },
            grid: {
                hoverable: true // IMPORTANT! this is needed for tooltip to work
            },
            tooltip: true,
            tooltipOpts: {
                content: "%s : Median Latency time at %x req/s was %y ms"
            },
            colors: ["#9ACD32", "#FF6347"]
        };
    },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesLatencyVsRequest"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotLatenciesVsRequest"), dataset, options);
        // setup overview
        $.plot($("#overviewLatenciesVsRequest"), dataset, prepareOverviewOptions(options));
    }
};

// Latencies vs Request
function refreshLatenciesVsRequest() {
        var infos = latenciesVsRequestInfos;
        prepareSeries(infos.data);
        if(isGraph($("#flotLatenciesVsRequest"))){
            infos.createGraph();
        }else{
            var choiceContainer = $("#choicesLatencyVsRequest");
            createLegend(choiceContainer, infos);
            infos.createGraph();
            setGraphZoomable("#flotLatenciesVsRequest", "#overviewLatenciesVsRequest");
            $('#footerLatenciesVsRequest .legendColorBox > div').each(function(i){
                $(this).clone().prependTo(choiceContainer.find("li").eq(i));
            });
        }
};

var hitsPerSecondInfos = {
        data: {"result": {"minY": 28.35, "minX": 1.79493684E12, "maxY": 120.81666666666666, "series": [{"data": [[1.79493684E12, 28.35], [1.7949369E12, 120.81666666666666]], "isOverall": false, "label": "hitsPerSecond", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.7949369E12, "title": "Hits Per Second"}},
        getOptions: function() {
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of hits / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendHitsPerSecond"
                },
                selection: {
                    mode : 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y.2 hits/sec"
                }
            };
        },
        createGraph: function createGraph() {
            var data = this.data;
            var dataset = prepareData(data.result.series, $("#choicesHitsPerSecond"));
            var options = this.getOptions();
            prepareOptions(options, data);
            $.plot($("#flotHitsPerSecond"), dataset, options);
            // setup overview
            $.plot($("#overviewHitsPerSecond"), dataset, prepareOverviewOptions(options));
        }
};

// Hits per second
function refreshHitsPerSecond(fixTimestamps) {
    var infos = hitsPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if (isGraph($("#flotHitsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesHitsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotHitsPerSecond", "#overviewHitsPerSecond");
        $('#footerHitsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
}

var codesPerSecondInfos = {
        data: {"result": {"minY": 27.333333333333332, "minX": 1.79493684E12, "maxY": 121.83333333333333, "series": [{"data": [[1.79493684E12, 27.333333333333332], [1.7949369E12, 121.83333333333333]], "isOverall": false, "label": "200", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.7949369E12, "title": "Codes Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of responses / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendCodesPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "Number of Response Codes %s at %x was %y.2 responses / sec"
                }
            };
        },
    createGraph: function() {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesCodesPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotCodesPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewCodesPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Codes per second
function refreshCodesPerSecond(fixTimestamps) {
    var infos = codesPerSecondInfos;
    prepareSeries(infos.data);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotCodesPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesCodesPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotCodesPerSecond", "#overviewCodesPerSecond");
        $('#footerCodesPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var transactionsPerSecondInfos = {
        data: {"result": {"minY": 27.333333333333332, "minX": 1.79493684E12, "maxY": 121.83333333333333, "series": [{"data": [[1.79493684E12, 27.333333333333332], [1.7949369E12, 121.83333333333333]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)-success", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.7949369E12, "title": "Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTransactionsPerSecond"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                }
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTransactionsPerSecond"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTransactionsPerSecond"), dataset, options);
        // setup overview
        $.plot($("#overviewTransactionsPerSecond"), dataset, prepareOverviewOptions(options));
    }
};

// Transactions per second
function refreshTransactionsPerSecond(fixTimestamps) {
    var infos = transactionsPerSecondInfos;
    prepareSeries(infos.data);
    if(infos.data.result.series.length == 0) {
        setEmptyGraph("#bodyTransactionsPerSecond");
        return;
    }
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotTransactionsPerSecond"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTransactionsPerSecond");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTransactionsPerSecond", "#overviewTransactionsPerSecond");
        $('#footerTransactionsPerSecond .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

var totalTPSInfos = {
        data: {"result": {"minY": 27.333333333333332, "minX": 1.79493684E12, "maxY": 121.83333333333333, "series": [{"data": [[1.79493684E12, 27.333333333333332], [1.7949369E12, 121.83333333333333]], "isOverall": false, "label": "Transaction-success", "isController": false}, {"data": [], "isOverall": false, "label": "Transaction-failure", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.7949369E12, "title": "Total Transactions Per Second"}},
        getOptions: function(){
            return {
                series: {
                    lines: {
                        show: true
                    },
                    points: {
                        show: true
                    }
                },
                xaxis: {
                    mode: "time",
                    timeformat: getTimeFormat(this.data.result.granularity),
                    axisLabel: getElapsedTimeLabel(this.data.result.granularity),
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20,
                },
                yaxis: {
                    axisLabel: "Number of transactions / sec",
                    axisLabelUseCanvas: true,
                    axisLabelFontSizePixels: 12,
                    axisLabelFontFamily: 'Verdana, Arial',
                    axisLabelPadding: 20
                },
                legend: {
                    noColumns: 2,
                    show: true,
                    container: "#legendTotalTPS"
                },
                selection: {
                    mode: 'xy'
                },
                grid: {
                    hoverable: true // IMPORTANT! this is needed for tooltip to
                                    // work
                },
                tooltip: true,
                tooltipOpts: {
                    content: "%s at %x was %y transactions / sec"
                },
                colors: ["#9ACD32", "#FF6347"]
            };
        },
    createGraph: function () {
        var data = this.data;
        var dataset = prepareData(data.result.series, $("#choicesTotalTPS"));
        var options = this.getOptions();
        prepareOptions(options, data);
        $.plot($("#flotTotalTPS"), dataset, options);
        // setup overview
        $.plot($("#overviewTotalTPS"), dataset, prepareOverviewOptions(options));
    }
};

// Total Transactions per second
function refreshTotalTPS(fixTimestamps) {
    var infos = totalTPSInfos;
    // We want to ignore seriesFilter
    prepareSeries(infos.data, false, true);
    if(fixTimestamps) {
        fixTimeStamps(infos.data.result.series, -18000000);
    }
    if(isGraph($("#flotTotalTPS"))){
        infos.createGraph();
    }else{
        var choiceContainer = $("#choicesTotalTPS");
        createLegend(choiceContainer, infos);
        infos.createGraph();
        setGraphZoomable("#flotTotalTPS", "#overviewTotalTPS");
        $('#footerTotalTPS .legendColorBox > div').each(function(i){
            $(this).clone().prependTo(choiceContainer.find("li").eq(i));
        });
    }
};

// Collapse the graph matching the specified DOM element depending the collapsed
// status
function collapse(elem, collapsed){
    if(collapsed){
        $(elem).parent().find(".fa-chevron-up").removeClass("fa-chevron-up").addClass("fa-chevron-down");
    } else {
        $(elem).parent().find(".fa-chevron-down").removeClass("fa-chevron-down").addClass("fa-chevron-up");
        if (elem.id == "bodyBytesThroughputOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshBytesThroughputOverTime(true);
            }
            document.location.href="#bytesThroughputOverTime";
        } else if (elem.id == "bodyLatenciesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesOverTime(true);
            }
            document.location.href="#latenciesOverTime";
        } else if (elem.id == "bodyCustomGraph") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCustomGraph(true);
            }
            document.location.href="#responseCustomGraph";
        } else if (elem.id == "bodyConnectTimeOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshConnectTimeOverTime(true);
            }
            document.location.href="#connectTimeOverTime";
        } else if (elem.id == "bodyResponseTimePercentilesOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimePercentilesOverTime(true);
            }
            document.location.href="#responseTimePercentilesOverTime";
        } else if (elem.id == "bodyResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeDistribution();
            }
            document.location.href="#responseTimeDistribution" ;
        } else if (elem.id == "bodySyntheticResponseTimeDistribution") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshSyntheticResponseTimeDistribution();
            }
            document.location.href="#syntheticResponseTimeDistribution" ;
        } else if (elem.id == "bodyActiveThreadsOverTime") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshActiveThreadsOverTime(true);
            }
            document.location.href="#activeThreadsOverTime";
        } else if (elem.id == "bodyTimeVsThreads") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTimeVsThreads();
            }
            document.location.href="#timeVsThreads" ;
        } else if (elem.id == "bodyCodesPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshCodesPerSecond(true);
            }
            document.location.href="#codesPerSecond";
        } else if (elem.id == "bodyTransactionsPerSecond") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTransactionsPerSecond(true);
            }
            document.location.href="#transactionsPerSecond";
        } else if (elem.id == "bodyTotalTPS") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshTotalTPS(true);
            }
            document.location.href="#totalTPS";
        } else if (elem.id == "bodyResponseTimeVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshResponseTimeVsRequest();
            }
            document.location.href="#responseTimeVsRequest";
        } else if (elem.id == "bodyLatenciesVsRequest") {
            if (isGraph($(elem).find('.flot-chart-content')) == false) {
                refreshLatenciesVsRequest();
            }
            document.location.href="#latencyVsRequest";
        }
    }
}

/*
 * Activates or deactivates all series of the specified graph (represented by id parameter)
 * depending on checked argument.
 */
function toggleAll(id, checked){
    var placeholder = document.getElementById(id);

    var cases = $(placeholder).find(':checkbox');
    cases.prop('checked', checked);
    $(cases).parent().children().children().toggleClass("legend-disabled", !checked);

    var choiceContainer;
    if ( id == "choicesBytesThroughputOverTime"){
        choiceContainer = $("#choicesBytesThroughputOverTime");
        refreshBytesThroughputOverTime(false);
    } else if(id == "choicesResponseTimesOverTime"){
        choiceContainer = $("#choicesResponseTimesOverTime");
        refreshResponseTimeOverTime(false);
    }else if(id == "choicesResponseCustomGraph"){
        choiceContainer = $("#choicesResponseCustomGraph");
        refreshCustomGraph(false);
    } else if ( id == "choicesLatenciesOverTime"){
        choiceContainer = $("#choicesLatenciesOverTime");
        refreshLatenciesOverTime(false);
    } else if ( id == "choicesConnectTimeOverTime"){
        choiceContainer = $("#choicesConnectTimeOverTime");
        refreshConnectTimeOverTime(false);
    } else if ( id == "choicesResponseTimePercentilesOverTime"){
        choiceContainer = $("#choicesResponseTimePercentilesOverTime");
        refreshResponseTimePercentilesOverTime(false);
    } else if ( id == "choicesResponseTimePercentiles"){
        choiceContainer = $("#choicesResponseTimePercentiles");
        refreshResponseTimePercentiles();
    } else if(id == "choicesActiveThreadsOverTime"){
        choiceContainer = $("#choicesActiveThreadsOverTime");
        refreshActiveThreadsOverTime(false);
    } else if ( id == "choicesTimeVsThreads"){
        choiceContainer = $("#choicesTimeVsThreads");
        refreshTimeVsThreads();
    } else if ( id == "choicesSyntheticResponseTimeDistribution"){
        choiceContainer = $("#choicesSyntheticResponseTimeDistribution");
        refreshSyntheticResponseTimeDistribution();
    } else if ( id == "choicesResponseTimeDistribution"){
        choiceContainer = $("#choicesResponseTimeDistribution");
        refreshResponseTimeDistribution();
    } else if ( id == "choicesHitsPerSecond"){
        choiceContainer = $("#choicesHitsPerSecond");
        refreshHitsPerSecond(false);
    } else if(id == "choicesCodesPerSecond"){
        choiceContainer = $("#choicesCodesPerSecond");
        refreshCodesPerSecond(false);
    } else if ( id == "choicesTransactionsPerSecond"){
        choiceContainer = $("#choicesTransactionsPerSecond");
        refreshTransactionsPerSecond(false);
    } else if ( id == "choicesTotalTPS"){
        choiceContainer = $("#choicesTotalTPS");
        refreshTotalTPS(false);
    } else if ( id == "choicesResponseTimeVsRequest"){
        choiceContainer = $("#choicesResponseTimeVsRequest");
        refreshResponseTimeVsRequest();
    } else if ( id == "choicesLatencyVsRequest"){
        choiceContainer = $("#choicesLatencyVsRequest");
        refreshLatenciesVsRequest();
    }
    var color = checked ? "black" : "#818181";
    if(choiceContainer != null) {
        choiceContainer.find("label").each(function(){
            this.style.color = color;
        });
    }
}

