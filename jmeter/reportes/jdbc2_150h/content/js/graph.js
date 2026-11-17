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
        data: {"result": {"minY": 12.0, "minX": 0.0, "maxY": 10012.0, "series": [{"data": [[0.0, 12.0], [0.1, 13.0], [0.2, 14.0], [0.3, 16.0], [0.4, 18.0], [0.5, 20.0], [0.6, 21.0], [0.7, 21.0], [0.8, 22.0], [0.9, 22.0], [1.0, 22.0], [1.1, 22.0], [1.2, 22.0], [1.3, 22.0], [1.4, 22.0], [1.5, 23.0], [1.6, 23.0], [1.7, 23.0], [1.8, 23.0], [1.9, 23.0], [2.0, 23.0], [2.1, 23.0], [2.2, 23.0], [2.3, 23.0], [2.4, 23.0], [2.5, 23.0], [2.6, 23.0], [2.7, 24.0], [2.8, 24.0], [2.9, 24.0], [3.0, 24.0], [3.1, 24.0], [3.2, 24.0], [3.3, 24.0], [3.4, 24.0], [3.5, 24.0], [3.6, 24.0], [3.7, 25.0], [3.8, 25.0], [3.9, 25.0], [4.0, 25.0], [4.1, 25.0], [4.2, 25.0], [4.3, 25.0], [4.4, 25.0], [4.5, 25.0], [4.6, 26.0], [4.7, 26.0], [4.8, 26.0], [4.9, 26.0], [5.0, 26.0], [5.1, 26.0], [5.2, 26.0], [5.3, 26.0], [5.4, 27.0], [5.5, 27.0], [5.6, 27.0], [5.7, 27.0], [5.8, 27.0], [5.9, 28.0], [6.0, 28.0], [6.1, 28.0], [6.2, 29.0], [6.3, 29.0], [6.4, 29.0], [6.5, 30.0], [6.6, 30.0], [6.7, 31.0], [6.8, 31.0], [6.9, 32.0], [7.0, 33.0], [7.1, 34.0], [7.2, 34.0], [7.3, 35.0], [7.4, 36.0], [7.5, 37.0], [7.6, 38.0], [7.7, 39.0], [7.8, 40.0], [7.9, 41.0], [8.0, 43.0], [8.1, 44.0], [8.2, 44.0], [8.3, 45.0], [8.4, 46.0], [8.5, 47.0], [8.6, 48.0], [8.7, 49.0], [8.8, 50.0], [8.9, 51.0], [9.0, 52.0], [9.1, 53.0], [9.2, 53.0], [9.3, 54.0], [9.4, 55.0], [9.5, 55.0], [9.6, 57.0], [9.7, 57.0], [9.8, 58.0], [9.9, 60.0], [10.0, 61.0], [10.1, 61.0], [10.2, 62.0], [10.3, 63.0], [10.4, 64.0], [10.5, 65.0], [10.6, 66.0], [10.7, 68.0], [10.8, 69.0], [10.9, 71.0], [11.0, 73.0], [11.1, 74.0], [11.2, 75.0], [11.3, 77.0], [11.4, 80.0], [11.5, 81.0], [11.6, 82.0], [11.7, 84.0], [11.8, 86.0], [11.9, 87.0], [12.0, 90.0], [12.1, 93.0], [12.2, 94.0], [12.3, 98.0], [12.4, 100.0], [12.5, 103.0], [12.6, 106.0], [12.7, 109.0], [12.8, 110.0], [12.9, 110.0], [13.0, 112.0], [13.1, 114.0], [13.2, 116.0], [13.3, 117.0], [13.4, 118.0], [13.5, 119.0], [13.6, 120.0], [13.7, 121.0], [13.8, 122.0], [13.9, 124.0], [14.0, 126.0], [14.1, 128.0], [14.2, 131.0], [14.3, 132.0], [14.4, 135.0], [14.5, 135.0], [14.6, 137.0], [14.7, 138.0], [14.8, 140.0], [14.9, 141.0], [15.0, 142.0], [15.1, 143.0], [15.2, 144.0], [15.3, 144.0], [15.4, 145.0], [15.5, 146.0], [15.6, 146.0], [15.7, 146.0], [15.8, 147.0], [15.9, 147.0], [16.0, 148.0], [16.1, 148.0], [16.2, 149.0], [16.3, 149.0], [16.4, 149.0], [16.5, 149.0], [16.6, 150.0], [16.7, 150.0], [16.8, 150.0], [16.9, 151.0], [17.0, 151.0], [17.1, 151.0], [17.2, 151.0], [17.3, 152.0], [17.4, 152.0], [17.5, 152.0], [17.6, 152.0], [17.7, 152.0], [17.8, 153.0], [17.9, 153.0], [18.0, 153.0], [18.1, 153.0], [18.2, 153.0], [18.3, 153.0], [18.4, 154.0], [18.5, 154.0], [18.6, 154.0], [18.7, 154.0], [18.8, 154.0], [18.9, 154.0], [19.0, 155.0], [19.1, 155.0], [19.2, 155.0], [19.3, 155.0], [19.4, 155.0], [19.5, 155.0], [19.6, 156.0], [19.7, 156.0], [19.8, 156.0], [19.9, 156.0], [20.0, 156.0], [20.1, 156.0], [20.2, 157.0], [20.3, 157.0], [20.4, 157.0], [20.5, 157.0], [20.6, 157.0], [20.7, 157.0], [20.8, 157.0], [20.9, 157.0], [21.0, 157.0], [21.1, 158.0], [21.2, 158.0], [21.3, 158.0], [21.4, 158.0], [21.5, 158.0], [21.6, 158.0], [21.7, 158.0], [21.8, 158.0], [21.9, 158.0], [22.0, 159.0], [22.1, 159.0], [22.2, 159.0], [22.3, 159.0], [22.4, 159.0], [22.5, 159.0], [22.6, 159.0], [22.7, 159.0], [22.8, 159.0], [22.9, 159.0], [23.0, 160.0], [23.1, 160.0], [23.2, 160.0], [23.3, 160.0], [23.4, 160.0], [23.5, 160.0], [23.6, 161.0], [23.7, 161.0], [23.8, 161.0], [23.9, 161.0], [24.0, 161.0], [24.1, 161.0], [24.2, 161.0], [24.3, 161.0], [24.4, 162.0], [24.5, 162.0], [24.6, 162.0], [24.7, 162.0], [24.8, 162.0], [24.9, 162.0], [25.0, 162.0], [25.1, 162.0], [25.2, 163.0], [25.3, 163.0], [25.4, 163.0], [25.5, 163.0], [25.6, 163.0], [25.7, 163.0], [25.8, 163.0], [25.9, 163.0], [26.0, 164.0], [26.1, 164.0], [26.2, 164.0], [26.3, 164.0], [26.4, 164.0], [26.5, 164.0], [26.6, 164.0], [26.7, 164.0], [26.8, 165.0], [26.9, 165.0], [27.0, 165.0], [27.1, 165.0], [27.2, 165.0], [27.3, 165.0], [27.4, 165.0], [27.5, 165.0], [27.6, 165.0], [27.7, 166.0], [27.8, 166.0], [27.9, 166.0], [28.0, 166.0], [28.1, 166.0], [28.2, 166.0], [28.3, 166.0], [28.4, 166.0], [28.5, 166.0], [28.6, 167.0], [28.7, 167.0], [28.8, 167.0], [28.9, 167.0], [29.0, 167.0], [29.1, 167.0], [29.2, 167.0], [29.3, 168.0], [29.4, 168.0], [29.5, 168.0], [29.6, 168.0], [29.7, 168.0], [29.8, 168.0], [29.9, 168.0], [30.0, 169.0], [30.1, 169.0], [30.2, 169.0], [30.3, 169.0], [30.4, 169.0], [30.5, 169.0], [30.6, 169.0], [30.7, 169.0], [30.8, 169.0], [30.9, 170.0], [31.0, 170.0], [31.1, 170.0], [31.2, 170.0], [31.3, 170.0], [31.4, 170.0], [31.5, 170.0], [31.6, 170.0], [31.7, 171.0], [31.8, 171.0], [31.9, 171.0], [32.0, 171.0], [32.1, 171.0], [32.2, 171.0], [32.3, 171.0], [32.4, 171.0], [32.5, 171.0], [32.6, 172.0], [32.7, 172.0], [32.8, 172.0], [32.9, 172.0], [33.0, 172.0], [33.1, 172.0], [33.2, 172.0], [33.3, 173.0], [33.4, 173.0], [33.5, 173.0], [33.6, 173.0], [33.7, 173.0], [33.8, 173.0], [33.9, 173.0], [34.0, 173.0], [34.1, 174.0], [34.2, 174.0], [34.3, 174.0], [34.4, 174.0], [34.5, 174.0], [34.6, 174.0], [34.7, 175.0], [34.8, 175.0], [34.9, 175.0], [35.0, 175.0], [35.1, 175.0], [35.2, 175.0], [35.3, 176.0], [35.4, 176.0], [35.5, 176.0], [35.6, 176.0], [35.7, 176.0], [35.8, 176.0], [35.9, 177.0], [36.0, 177.0], [36.1, 177.0], [36.2, 177.0], [36.3, 177.0], [36.4, 178.0], [36.5, 178.0], [36.6, 178.0], [36.7, 178.0], [36.8, 178.0], [36.9, 179.0], [37.0, 179.0], [37.1, 179.0], [37.2, 179.0], [37.3, 179.0], [37.4, 179.0], [37.5, 179.0], [37.6, 179.0], [37.7, 180.0], [37.8, 180.0], [37.9, 180.0], [38.0, 180.0], [38.1, 180.0], [38.2, 180.0], [38.3, 180.0], [38.4, 181.0], [38.5, 181.0], [38.6, 181.0], [38.7, 181.0], [38.8, 181.0], [38.9, 181.0], [39.0, 181.0], [39.1, 182.0], [39.2, 182.0], [39.3, 182.0], [39.4, 182.0], [39.5, 182.0], [39.6, 183.0], [39.7, 183.0], [39.8, 183.0], [39.9, 183.0], [40.0, 183.0], [40.1, 183.0], [40.2, 184.0], [40.3, 184.0], [40.4, 184.0], [40.5, 184.0], [40.6, 184.0], [40.7, 184.0], [40.8, 185.0], [40.9, 185.0], [41.0, 185.0], [41.1, 185.0], [41.2, 185.0], [41.3, 186.0], [41.4, 186.0], [41.5, 186.0], [41.6, 186.0], [41.7, 187.0], [41.8, 187.0], [41.9, 187.0], [42.0, 187.0], [42.1, 188.0], [42.2, 188.0], [42.3, 188.0], [42.4, 188.0], [42.5, 189.0], [42.6, 189.0], [42.7, 189.0], [42.8, 189.0], [42.9, 190.0], [43.0, 190.0], [43.1, 190.0], [43.2, 190.0], [43.3, 191.0], [43.4, 191.0], [43.5, 191.0], [43.6, 192.0], [43.7, 192.0], [43.8, 192.0], [43.9, 192.0], [44.0, 193.0], [44.1, 193.0], [44.2, 193.0], [44.3, 194.0], [44.4, 194.0], [44.5, 195.0], [44.6, 195.0], [44.7, 195.0], [44.8, 196.0], [44.9, 196.0], [45.0, 197.0], [45.1, 197.0], [45.2, 198.0], [45.3, 198.0], [45.4, 198.0], [45.5, 199.0], [45.6, 200.0], [45.7, 201.0], [45.8, 201.0], [45.9, 202.0], [46.0, 203.0], [46.1, 204.0], [46.2, 204.0], [46.3, 205.0], [46.4, 206.0], [46.5, 207.0], [46.6, 207.0], [46.7, 208.0], [46.8, 210.0], [46.9, 211.0], [47.0, 212.0], [47.1, 213.0], [47.2, 214.0], [47.3, 214.0], [47.4, 216.0], [47.5, 217.0], [47.6, 219.0], [47.7, 220.0], [47.8, 223.0], [47.9, 225.0], [48.0, 227.0], [48.1, 229.0], [48.2, 230.0], [48.3, 233.0], [48.4, 237.0], [48.5, 241.0], [48.6, 248.0], [48.7, 257.0], [48.8, 271.0], [48.9, 275.0], [49.0, 288.0], [49.1, 295.0], [49.2, 305.0], [49.3, 310.0], [49.4, 317.0], [49.5, 327.0], [49.6, 344.0], [49.7, 375.0], [49.8, 398.0], [49.9, 425.0], [50.0, 442.0], [50.1, 472.0], [50.2, 506.0], [50.3, 529.0], [50.4, 548.0], [50.5, 563.0], [50.6, 569.0], [50.7, 577.0], [50.8, 581.0], [50.9, 588.0], [51.0, 591.0], [51.1, 596.0], [51.2, 603.0], [51.3, 608.0], [51.4, 613.0], [51.5, 622.0], [51.6, 632.0], [51.7, 646.0], [51.8, 662.0], [51.9, 668.0], [52.0, 673.0], [52.1, 677.0], [52.2, 682.0], [52.3, 684.0], [52.4, 687.0], [52.5, 691.0], [52.6, 692.0], [52.7, 695.0], [52.8, 700.0], [52.9, 704.0], [53.0, 708.0], [53.1, 712.0], [53.2, 715.0], [53.3, 721.0], [53.4, 724.0], [53.5, 729.0], [53.6, 743.0], [53.7, 748.0], [53.8, 761.0], [53.9, 773.0], [54.0, 776.0], [54.1, 781.0], [54.2, 783.0], [54.3, 784.0], [54.4, 786.0], [54.5, 788.0], [54.6, 789.0], [54.7, 790.0], [54.8, 793.0], [54.9, 793.0], [55.0, 794.0], [55.1, 795.0], [55.2, 795.0], [55.3, 796.0], [55.4, 798.0], [55.5, 798.0], [55.6, 799.0], [55.7, 800.0], [55.8, 800.0], [55.9, 801.0], [56.0, 801.0], [56.1, 802.0], [56.2, 803.0], [56.3, 804.0], [56.4, 805.0], [56.5, 805.0], [56.6, 806.0], [56.7, 806.0], [56.8, 807.0], [56.9, 808.0], [57.0, 808.0], [57.1, 809.0], [57.2, 809.0], [57.3, 810.0], [57.4, 811.0], [57.5, 812.0], [57.6, 812.0], [57.7, 813.0], [57.8, 814.0], [57.9, 814.0], [58.0, 815.0], [58.1, 815.0], [58.2, 816.0], [58.3, 816.0], [58.4, 816.0], [58.5, 817.0], [58.6, 817.0], [58.7, 818.0], [58.8, 818.0], [58.9, 819.0], [59.0, 819.0], [59.1, 819.0], [59.2, 820.0], [59.3, 821.0], [59.4, 821.0], [59.5, 821.0], [59.6, 822.0], [59.7, 822.0], [59.8, 823.0], [59.9, 823.0], [60.0, 824.0], [60.1, 824.0], [60.2, 825.0], [60.3, 825.0], [60.4, 825.0], [60.5, 826.0], [60.6, 826.0], [60.7, 826.0], [60.8, 827.0], [60.9, 827.0], [61.0, 827.0], [61.1, 828.0], [61.2, 828.0], [61.3, 829.0], [61.4, 829.0], [61.5, 829.0], [61.6, 830.0], [61.7, 830.0], [61.8, 830.0], [61.9, 831.0], [62.0, 831.0], [62.1, 831.0], [62.2, 832.0], [62.3, 832.0], [62.4, 833.0], [62.5, 833.0], [62.6, 833.0], [62.7, 834.0], [62.8, 834.0], [62.9, 834.0], [63.0, 835.0], [63.1, 835.0], [63.2, 835.0], [63.3, 836.0], [63.4, 836.0], [63.5, 837.0], [63.6, 837.0], [63.7, 837.0], [63.8, 838.0], [63.9, 838.0], [64.0, 838.0], [64.1, 839.0], [64.2, 839.0], [64.3, 839.0], [64.4, 839.0], [64.5, 840.0], [64.6, 840.0], [64.7, 841.0], [64.8, 841.0], [64.9, 841.0], [65.0, 841.0], [65.1, 842.0], [65.2, 842.0], [65.3, 842.0], [65.4, 843.0], [65.5, 843.0], [65.6, 843.0], [65.7, 844.0], [65.8, 844.0], [65.9, 844.0], [66.0, 845.0], [66.1, 845.0], [66.2, 845.0], [66.3, 846.0], [66.4, 846.0], [66.5, 846.0], [66.6, 846.0], [66.7, 847.0], [66.8, 847.0], [66.9, 847.0], [67.0, 847.0], [67.1, 848.0], [67.2, 848.0], [67.3, 848.0], [67.4, 848.0], [67.5, 848.0], [67.6, 849.0], [67.7, 849.0], [67.8, 849.0], [67.9, 849.0], [68.0, 850.0], [68.1, 850.0], [68.2, 850.0], [68.3, 851.0], [68.4, 851.0], [68.5, 851.0], [68.6, 851.0], [68.7, 852.0], [68.8, 852.0], [68.9, 852.0], [69.0, 852.0], [69.1, 853.0], [69.2, 853.0], [69.3, 853.0], [69.4, 854.0], [69.5, 854.0], [69.6, 854.0], [69.7, 854.0], [69.8, 854.0], [69.9, 855.0], [70.0, 855.0], [70.1, 855.0], [70.2, 856.0], [70.3, 856.0], [70.4, 856.0], [70.5, 856.0], [70.6, 856.0], [70.7, 857.0], [70.8, 857.0], [70.9, 857.0], [71.0, 858.0], [71.1, 858.0], [71.2, 858.0], [71.3, 858.0], [71.4, 859.0], [71.5, 859.0], [71.6, 859.0], [71.7, 860.0], [71.8, 860.0], [71.9, 860.0], [72.0, 860.0], [72.1, 861.0], [72.2, 861.0], [72.3, 862.0], [72.4, 862.0], [72.5, 862.0], [72.6, 863.0], [72.7, 863.0], [72.8, 863.0], [72.9, 864.0], [73.0, 864.0], [73.1, 864.0], [73.2, 864.0], [73.3, 865.0], [73.4, 865.0], [73.5, 865.0], [73.6, 865.0], [73.7, 866.0], [73.8, 867.0], [73.9, 867.0], [74.0, 867.0], [74.1, 868.0], [74.2, 868.0], [74.3, 868.0], [74.4, 868.0], [74.5, 869.0], [74.6, 869.0], [74.7, 869.0], [74.8, 870.0], [74.9, 870.0], [75.0, 870.0], [75.1, 870.0], [75.2, 871.0], [75.3, 871.0], [75.4, 871.0], [75.5, 872.0], [75.6, 872.0], [75.7, 872.0], [75.8, 873.0], [75.9, 873.0], [76.0, 873.0], [76.1, 874.0], [76.2, 874.0], [76.3, 875.0], [76.4, 876.0], [76.5, 876.0], [76.6, 876.0], [76.7, 877.0], [76.8, 877.0], [76.9, 878.0], [77.0, 878.0], [77.1, 879.0], [77.2, 879.0], [77.3, 879.0], [77.4, 880.0], [77.5, 881.0], [77.6, 881.0], [77.7, 881.0], [77.8, 882.0], [77.9, 883.0], [78.0, 884.0], [78.1, 884.0], [78.2, 885.0], [78.3, 885.0], [78.4, 886.0], [78.5, 886.0], [78.6, 887.0], [78.7, 887.0], [78.8, 888.0], [78.9, 889.0], [79.0, 889.0], [79.1, 890.0], [79.2, 891.0], [79.3, 891.0], [79.4, 892.0], [79.5, 893.0], [79.6, 893.0], [79.7, 894.0], [79.8, 895.0], [79.9, 895.0], [80.0, 896.0], [80.1, 897.0], [80.2, 898.0], [80.3, 898.0], [80.4, 899.0], [80.5, 901.0], [80.6, 901.0], [80.7, 902.0], [80.8, 903.0], [80.9, 904.0], [81.0, 905.0], [81.1, 906.0], [81.2, 906.0], [81.3, 907.0], [81.4, 908.0], [81.5, 909.0], [81.6, 911.0], [81.7, 912.0], [81.8, 913.0], [81.9, 914.0], [82.0, 915.0], [82.1, 916.0], [82.2, 917.0], [82.3, 919.0], [82.4, 920.0], [82.5, 921.0], [82.6, 923.0], [82.7, 924.0], [82.8, 925.0], [82.9, 927.0], [83.0, 930.0], [83.1, 931.0], [83.2, 934.0], [83.3, 935.0], [83.4, 938.0], [83.5, 940.0], [83.6, 942.0], [83.7, 944.0], [83.8, 945.0], [83.9, 948.0], [84.0, 949.0], [84.1, 952.0], [84.2, 954.0], [84.3, 956.0], [84.4, 958.0], [84.5, 960.0], [84.6, 962.0], [84.7, 965.0], [84.8, 969.0], [84.9, 970.0], [85.0, 973.0], [85.1, 975.0], [85.2, 977.0], [85.3, 980.0], [85.4, 983.0], [85.5, 986.0], [85.6, 987.0], [85.7, 988.0], [85.8, 991.0], [85.9, 993.0], [86.0, 995.0], [86.1, 998.0], [86.2, 1002.0], [86.3, 1005.0], [86.4, 1008.0], [86.5, 1011.0], [86.6, 1014.0], [86.7, 1019.0], [86.8, 1025.0], [86.9, 1030.0], [87.0, 1040.0], [87.1, 1065.0], [87.2, 1179.0], [87.3, 1202.0], [87.4, 1223.0], [87.5, 1234.0], [87.6, 1296.0], [87.7, 1346.0], [87.8, 1392.0], [87.9, 1423.0], [88.0, 1442.0], [88.1, 1446.0], [88.2, 1457.0], [88.3, 1466.0], [88.4, 1471.0], [88.5, 1478.0], [88.6, 1483.0], [88.7, 1492.0], [88.8, 1498.0], [88.9, 1500.0], [89.0, 1505.0], [89.1, 1510.0], [89.2, 1512.0], [89.3, 1516.0], [89.4, 1522.0], [89.5, 1525.0], [89.6, 1528.0], [89.7, 1530.0], [89.8, 1531.0], [89.9, 1534.0], [90.0, 1536.0], [90.1, 1538.0], [90.2, 1541.0], [90.3, 1543.0], [90.4, 1544.0], [90.5, 1546.0], [90.6, 1551.0], [90.7, 1556.0], [90.8, 1558.0], [90.9, 1560.0], [91.0, 1562.0], [91.1, 1566.0], [91.2, 1568.0], [91.3, 1572.0], [91.4, 1575.0], [91.5, 1579.0], [91.6, 1584.0], [91.7, 1587.0], [91.8, 1595.0], [91.9, 1611.0], [92.0, 1627.0], [92.1, 1640.0], [92.2, 1653.0], [92.3, 1662.0], [92.4, 1672.0], [92.5, 1679.0], [92.6, 1688.0], [92.7, 1698.0], [92.8, 1710.0], [92.9, 1719.0], [93.0, 1733.0], [93.1, 1762.0], [93.2, 1865.0], [93.3, 1949.0], [93.4, 2084.0], [93.5, 2103.0], [93.6, 2113.0], [93.7, 2127.0], [93.8, 2151.0], [93.9, 2166.0], [94.0, 2174.0], [94.1, 2186.0], [94.2, 2200.0], [94.3, 2209.0], [94.4, 2218.0], [94.5, 2230.0], [94.6, 2235.0], [94.7, 2249.0], [94.8, 2256.0], [94.9, 2276.0], [95.0, 2316.0], [95.1, 2344.0], [95.2, 2371.0], [95.3, 2401.0], [95.4, 2428.0], [95.5, 2486.0], [95.6, 2600.0], [95.7, 2779.0], [95.8, 2809.0], [95.9, 2832.0], [96.0, 2848.0], [96.1, 2872.0], [96.2, 2895.0], [96.3, 2906.0], [96.4, 2915.0], [96.5, 2924.0], [96.6, 2936.0], [96.7, 2953.0], [96.8, 2972.0], [96.9, 3000.0], [97.0, 3081.0], [97.1, 3123.0], [97.2, 3428.0], [97.3, 3479.0], [97.4, 3505.0], [97.5, 3579.0], [97.6, 3606.0], [97.7, 3644.0], [97.8, 3707.0], [97.9, 3857.0], [98.0, 4130.0], [98.1, 4185.0], [98.2, 4267.0], [98.3, 4291.0], [98.4, 4320.0], [98.5, 4370.0], [98.6, 4556.0], [98.7, 4788.0], [98.8, 4947.0], [98.9, 5028.0], [99.0, 5106.0], [99.1, 5379.0], [99.2, 5518.0], [99.3, 5704.0], [99.4, 5979.0], [99.5, 6419.0], [99.6, 6803.0], [99.7, 7493.0], [99.8, 8021.0], [99.9, 9024.0], [100.0, 10012.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 100.0, "title": "Response Time Percentiles"}},
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
        data: {"result": {"minY": 1.0, "minX": 0.0, "maxY": 2797.0, "series": [{"data": [[0.0, 1043.0], [600.0, 134.0], [700.0, 244.0], [800.0, 2088.0], [900.0, 483.0], [1000.0, 82.0], [1100.0, 13.0], [1200.0, 27.0], [1300.0, 18.0], [1400.0, 90.0], [1500.0, 249.0], [1600.0, 75.0], [1700.0, 35.0], [1800.0, 8.0], [1900.0, 7.0], [2000.0, 14.0], [2100.0, 59.0], [2200.0, 67.0], [2300.0, 25.0], [2400.0, 22.0], [2500.0, 4.0], [2600.0, 2.0], [2700.0, 11.0], [2800.0, 41.0], [2900.0, 56.0], [3000.0, 14.0], [3100.0, 8.0], [3300.0, 1.0], [3200.0, 1.0], [3400.0, 16.0], [3500.0, 17.0], [3600.0, 17.0], [3700.0, 6.0], [3800.0, 9.0], [4000.0, 1.0], [4100.0, 12.0], [4200.0, 19.0], [4300.0, 17.0], [4500.0, 6.0], [4400.0, 2.0], [4700.0, 7.0], [4800.0, 7.0], [5100.0, 7.0], [5000.0, 11.0], [4900.0, 6.0], [5200.0, 2.0], [5300.0, 1.0], [5600.0, 6.0], [5500.0, 4.0], [5400.0, 5.0], [5700.0, 5.0], [5800.0, 3.0], [5900.0, 2.0], [6100.0, 3.0], [6000.0, 1.0], [6300.0, 3.0], [6500.0, 5.0], [6400.0, 2.0], [6900.0, 1.0], [6800.0, 2.0], [6700.0, 2.0], [7000.0, 4.0], [7400.0, 2.0], [7600.0, 3.0], [7500.0, 1.0], [7700.0, 3.0], [7900.0, 1.0], [8000.0, 1.0], [8100.0, 1.0], [8600.0, 1.0], [8300.0, 1.0], [9100.0, 1.0], [9200.0, 2.0], [9000.0, 1.0], [8800.0, 4.0], [10000.0, 4.0], [9900.0, 1.0], [100.0, 2797.0], [200.0, 305.0], [300.0, 55.0], [400.0, 31.0], [500.0, 86.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 100, "maxX": 10000.0, "title": "Response Time Distribution"}},
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
        data: {"result": {"minY": 4.0, "minX": 0.0, "ticks": [[0, "Requests having \nresponse time <= 500ms"], [1, "Requests having \nresponse time > 500ms and <= 1,500ms"], [2, "Requests having \nresponse time > 1,500ms"], [3, "Requests in error"]], "maxY": 4231.0, "series": [{"data": [[0.0, 4231.0]], "color": "#9ACD32", "isOverall": false, "label": "Requests having \nresponse time <= 500ms", "isController": false}, {"data": [[1.0, 3267.0]], "color": "yellow", "isOverall": false, "label": "Requests having \nresponse time > 500ms and <= 1,500ms", "isController": false}, {"data": [[2.0, 931.0]], "color": "orange", "isOverall": false, "label": "Requests having \nresponse time > 1,500ms", "isController": false}, {"data": [[3.0, 4.0]], "color": "#FF6347", "isOverall": false, "label": "Requests in error", "isController": false}], "supportsControllersDiscrimination": false, "maxX": 3.0, "title": "Synthetic Response Times Distribution"}},
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
        data: {"result": {"minY": 91.40635451505017, "minX": 1.7949369E12, "maxY": 148.15196159576226, "series": [{"data": [[1.79493696E12, 148.15196159576226], [1.7949369E12, 91.40635451505017]], "isOverall": false, "label": "Hilos JDBC", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79493696E12, "title": "Active Threads Over Time"}},
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
        data: {"result": {"minY": 63.17073170731708, "minX": 1.0, "maxY": 8833.0, "series": [{"data": [[2.0, 6093.0], [4.0, 2767.5], [6.0, 2447.5], [8.0, 1497.0], [9.0, 2454.5], [10.0, 4119.0], [12.0, 813.0], [13.0, 829.0], [14.0, 3479.0], [15.0, 863.0], [16.0, 827.0], [17.0, 851.0], [18.0, 3464.0], [19.0, 859.0], [20.0, 3457.0], [21.0, 856.0], [22.0, 862.0], [23.0, 2841.0], [24.0, 831.0], [25.0, 2185.0], [26.0, 2832.0], [28.0, 6476.0], [29.0, 865.0], [30.0, 855.0], [31.0, 2842.0], [33.0, 1522.0], [32.0, 842.0], [35.0, 2159.5], [36.0, 1510.0], [39.0, 837.0], [38.0, 1861.5], [41.0, 1518.0], [43.0, 860.0], [42.0, 862.0], [45.0, 1566.0], [44.0, 879.0], [47.0, 2199.0], [46.0, 851.0], [49.0, 8833.0], [48.0, 867.0], [51.0, 707.3287671232875], [50.0, 3471.0], [52.0, 284.7222222222222], [53.0, 4122.0], [54.0, 584.4799999999998], [55.0, 113.13513513513513], [56.0, 374.8536585365854], [57.0, 193.58536585365857], [58.0, 120.38461538461539], [59.0, 64.8], [60.0, 135.58139534883722], [61.0, 63.17073170731708], [62.0, 158.04444444444442], [63.0, 153.4090909090909], [64.0, 143.69767441860463], [65.0, 67.3170731707317], [66.0, 187.17500000000004], [67.0, 87.56521739130434], [68.0, 98.15789473684211], [69.0, 97.02083333333336], [70.0, 121.85365853658537], [71.0, 166.5454545454546], [72.0, 69.1], [73.0, 107.02857142857144], [74.0, 82.3409090909091], [75.0, 105.1111111111111], [76.0, 247.94594594594588], [77.0, 738.4722222222222], [78.0, 570.088888888889], [79.0, 251.2666666666667], [80.0, 271.8095238095238], [81.0, 352.4761904761904], [82.0, 114.67567567567568], [83.0, 301.5], [84.0, 143.6969696969697], [85.0, 189.40000000000003], [86.0, 183.25], [87.0, 188.0810810810811], [88.0, 260.2368421052632], [89.0, 171.17857142857144], [90.0, 208.26086956521738], [91.0, 226.63636363636365], [92.0, 203.28571428571428], [93.0, 225.75], [94.0, 333.00000000000006], [95.0, 388.2], [96.0, 288.18181818181813], [97.0, 545.1250000000001], [98.0, 429.92307692307696], [99.0, 489.7], [100.0, 582.3636363636364], [101.0, 425.5], [102.0, 523.1538461538462], [103.0, 1020.1538461538462], [104.0, 518.8], [105.0, 478.8947368421052], [106.0, 574.5], [107.0, 461.58333333333337], [108.0, 855.3571428571429], [109.0, 504.6923076923077], [110.0, 610.1999999999999], [111.0, 1201.4], [112.0, 1107.5], [113.0, 768.9375], [114.0, 809.8181818181818], [115.0, 676.9166666666666], [116.0, 687.8571428571428], [117.0, 623.8181818181818], [118.0, 954.5], [119.0, 1130.5333333333333], [120.0, 971.9090909090909], [121.0, 687.5], [122.0, 804.6363636363636], [123.0, 457.909090909091], [124.0, 665.7777777777778], [125.0, 657.7777777777778], [126.0, 679.9090909090909], [127.0, 530.1999999999999], [128.0, 990.2727272727275], [129.0, 724.6000000000001], [130.0, 638.7272727272727], [131.0, 520.7142857142858], [132.0, 994.2], [133.0, 989.8000000000001], [134.0, 836.7333333333336], [135.0, 952.75], [136.0, 518.0], [137.0, 467.46153846153845], [138.0, 876.0833333333334], [139.0, 533.6428571428571], [140.0, 610.3125], [141.0, 640.875], [142.0, 618.4000000000001], [143.0, 586.7692307692307], [144.0, 558.7857142857143], [145.0, 505.7692307692307], [146.0, 591.2307692307693], [147.0, 777.5999999999999], [148.0, 869.1], [149.0, 855.5714285714286], [150.0, 842.9942509855449], [1.0, 733.0]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}, {"data": [[132.05620775524662, 720.2311158543797]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)-Aggregated", "isController": false}], "supportsControllersDiscrimination": true, "maxX": 150.0, "title": "Time VS Threads"}},
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
        data : {"result": {"minY": 0.0, "minX": 1.7949369E12, "maxY": 98912.58333333333, "series": [{"data": [[1.79493696E12, 98912.58333333333], [1.7949369E12, 39188.933333333334]], "isOverall": false, "label": "Bytes received per second", "isController": false}, {"data": [[1.79493696E12, 0.0], [1.7949369E12, 0.0]], "isOverall": false, "label": "Bytes sent per second", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79493696E12, "title": "Bytes Throughput Over Time"}},
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
        data: {"result": {"minY": 334.19941471571906, "minX": 1.7949369E12, "maxY": 873.0845886442638, "series": [{"data": [[1.79493696E12, 873.0845886442638], [1.7949369E12, 334.19941471571906]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79493696E12, "title": "Response Time Over Time"}},
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
        data: {"result": {"minY": 333.1354515050171, "minX": 1.7949369E12, "maxY": 866.3550736632992, "series": [{"data": [[1.79493696E12, 866.3550736632992], [1.7949369E12, 333.1354515050171]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79493696E12, "title": "Latencies Over Time"}},
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
        data: {"result": {"minY": 237.83653846153894, "minX": 1.7949369E12, "maxY": 700.6040390663785, "series": [{"data": [[1.79493696E12, 700.6040390663785], [1.7949369E12, 237.83653846153894]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79493696E12, "title": "Connect Time Over Time"}},
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
        data: {"result": {"minY": 12.0, "minX": 1.7949369E12, "maxY": 9905.0, "series": [{"data": [[1.79493696E12, 9905.0], [1.7949369E12, 4816.0]], "isOverall": false, "label": "Max", "isController": false}, {"data": [[1.79493696E12, 20.0], [1.7949369E12, 12.0]], "isOverall": false, "label": "Min", "isController": false}, {"data": [[1.79493696E12, 1621.5999999999995], [1.7949369E12, 845.4000000000005]], "isOverall": false, "label": "90th percentile", "isController": false}, {"data": [[1.79493696E12, 5672.959999999999], [1.7949369E12, 2389.6300000000015]], "isOverall": false, "label": "99th percentile", "isController": false}, {"data": [[1.79493696E12, 828.0], [1.7949369E12, 132.0]], "isOverall": false, "label": "Median", "isController": false}, {"data": [[1.79493696E12, 2895.399999999998], [1.7949369E12, 1346.35]], "isOverall": false, "label": "95th percentile", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79493696E12, "title": "Response Time Percentiles Over Time (successful requests only)"}},
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
    data: {"result": {"minY": 33.0, "minX": 133.0, "maxY": 10012.0, "series": [{"data": [[592.0, 42.0], [133.0, 865.0], [150.0, 887.5], [152.0, 967.5], [166.0, 609.5], [163.0, 921.0], [161.0, 798.0], [165.0, 955.0], [172.0, 386.5], [174.0, 786.0], [169.0, 863.0], [175.0, 848.0], [173.0, 861.0], [182.0, 692.0], [180.0, 846.5], [176.0, 835.0], [179.0, 828.5], [181.0, 796.0], [183.0, 847.0], [177.0, 210.5], [178.0, 199.5], [185.0, 788.5], [189.0, 180.0], [184.0, 773.0], [450.0, 33.0], [490.0, 132.0]], "isOverall": false, "label": "Successes", "isController": false}, {"data": [[165.0, 10005.0], [173.0, 10012.0], [182.0, 10004.0], [177.0, 10007.0]], "isOverall": false, "label": "Failures", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 592.0, "title": "Response Time Vs Request"}},
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
    data: {"result": {"minY": 0.0, "minX": 133.0, "maxY": 967.5, "series": [{"data": [[592.0, 41.0], [133.0, 865.0], [150.0, 887.5], [152.0, 967.5], [166.0, 609.0], [163.0, 921.0], [161.0, 798.0], [165.0, 955.0], [172.0, 386.0], [174.0, 786.0], [169.0, 863.0], [175.0, 848.0], [173.0, 861.0], [182.0, 692.0], [180.0, 846.0], [176.0, 835.0], [179.0, 828.0], [181.0, 796.0], [183.0, 847.0], [177.0, 210.5], [178.0, 199.5], [185.0, 788.5], [189.0, 180.0], [184.0, 772.5], [450.0, 33.0], [490.0, 131.5]], "isOverall": false, "label": "Successes", "isController": false}, {"data": [[165.0, 0.0], [173.0, 0.0], [182.0, 0.0], [177.0, 0.0]], "isOverall": false, "label": "Failures", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 1000, "maxX": 592.0, "title": "Latencies Vs Request"}},
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
        data: {"result": {"minY": 42.36666666666667, "minX": 1.7949369E12, "maxY": 98.18333333333334, "series": [{"data": [[1.79493696E12, 98.18333333333334], [1.7949369E12, 42.36666666666667]], "isOverall": false, "label": "hitsPerSecond", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79493696E12, "title": "Hits Per Second"}},
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
        data: {"result": {"minY": 0.06666666666666667, "minX": 1.7949369E12, "maxY": 100.61666666666666, "series": [{"data": [[1.79493696E12, 100.61666666666666], [1.7949369E12, 39.86666666666667]], "isOverall": false, "label": "200", "isController": false}, {"data": [[1.79493696E12, 0.06666666666666667]], "isOverall": false, "label": "null 0", "isController": false}], "supportsControllersDiscrimination": false, "granularity": 60000, "maxX": 1.79493696E12, "title": "Codes Per Second"}},
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
        data: {"result": {"minY": 0.06666666666666667, "minX": 1.7949369E12, "maxY": 100.61666666666666, "series": [{"data": [[1.79493696E12, 100.61666666666666], [1.7949369E12, 39.86666666666667]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)-success", "isController": false}, {"data": [[1.79493696E12, 0.06666666666666667]], "isOverall": false, "label": "Controles mas incumplidos (JOIN + GROUP BY)-failure", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79493696E12, "title": "Transactions Per Second"}},
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
        data: {"result": {"minY": 0.06666666666666667, "minX": 1.7949369E12, "maxY": 100.61666666666666, "series": [{"data": [[1.79493696E12, 100.61666666666666], [1.7949369E12, 39.86666666666667]], "isOverall": false, "label": "Transaction-success", "isController": false}, {"data": [[1.79493696E12, 0.06666666666666667]], "isOverall": false, "label": "Transaction-failure", "isController": false}], "supportsControllersDiscrimination": true, "granularity": 60000, "maxX": 1.79493696E12, "title": "Total Transactions Per Second"}},
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

