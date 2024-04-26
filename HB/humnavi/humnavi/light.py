import asyncio
import spidev  # SPI通信用のモジュールをインポート

# SPI通信を行うための準備
spi = spidev.SpiDev()  # インスタンスを生成
spi.open(0, 0)  # CE0(24番ピン)を指定
spi.max_speed_hz = 1000000  # 転送速度 1MHz


# 連続して値を読み込む
class LightSensor:
    def __init__(self):
        print("LightSensor initialized")
        self.is_armopen = False

    """ depricated but left for record
    async def cycle_light_legacy(self, num_keep_value: int, sigma: float) -> None:
        num_cycle = 1
        q = queue.Queue()
        while True:
            resp = spi.xfer2([0x68, 0x00])  # SPI通信で値を読み込む
            volume = ((resp[0] << 8) + resp[1]) & 0x3FF  # 読み込んだ値を10ビットの数値に変換

            if num_cycle == 1:
                q = queue.Queue()
                q.put(volume)
                ave_volume = volume
                sigma_volume = 0
            elif num_cycle <= num_keep_value:
                q.put(volume)
                ave_volume = (ave_volume * (num_cycle - 1) + volume) / num_cycle
                print(f"average: {ave_volume}")
                sigma_volume = np.sqrt(
                    ((sigma_volume**2 * (num_cycle - 1)) + (volume - ave_volume) ** 2)
                    / num_cycle
                )
                print(f"square_average:{sigma_volume}")
                q.get()
            else:
                q.put(volume)
                ave_volume = (
                    ave_volume * (num_keep_value - 1) + volume
                ) / num_keep_value
                print(f"average: {ave_volume}")
                sigma_volume = np.sqrt(
                    (
                        (sigma_volume**2 * (num_keep_value - 1))
                        + (volume - ave_volume) ** 2
                    )
                    / num_keep_value
                )
                print(f"square_average:{sigma_volume}")
            if abs(volume - ave_volume) > sigma * sigma_volume:
                self.is_armopen = True
                print("arm_is_opened!")
                break
            num_cycle += 1
            await asyncio.sleep(0.02)  # 1秒間待つ
    """

    async def cycle_light_naive(self, threshold: int) -> None:
        cycle_idx = 0
        while True:
            resp = spi.xfer2([0x68, 0x00])  # SPI通信で値を読み込む
            volume = ((resp[0] << 8) + resp[1]) & 0x3FF  # 読み込んだ値を10ビットの数値に変換
            if cycle_idx == 0:
                ave_volume = volume
            else:
                total_volume = ave_volume * (cycle_idx - 1) + volume
                ave_volume = total_volume / cycle_idx
                print(volume, ave_volume)
                if (volume - ave_volume) > threshold:
                    self.is_armopen = True
                    print("arm_is_opened!")
                    break
            cycle_idx += 1
            await asyncio.sleep(0.02)

    async def cycle_light_naive_carefully(self, threshold: int) -> None:
        cycle_idx = 0
        detect_ave_times = 5
        stand_ave_times = detect_ave_times * 10
        while True:
            resp = spi.xfer2([0x68, 0x00])  # SPI通信で値を読み込む
            volume = ((resp[0] << 8) + resp[1]) & 0x3FF  # 読み込んだ値を10ビットの数値に変換
            if cycle_idx == 0:
                stand_volume = [volume for _ in range(stand_ave_times)]
                detect_volume = [volume for _ in range(detect_ave_times)]
            else:
                stand_volume[cycle_idx % stand_ave_times] = volume
                detect_volume[cycle_idx % detect_ave_times] = volume
                print(
                    sum(detect_volume) / len(detect_volume),
                    sum(stand_volume) / len(stand_volume),
                )
                if (
                    sum(detect_volume) / len(detect_volume)
                    - sum(stand_volume) / len(stand_volume)
                ) > threshold:
                    self.is_armopen = True
                    print("arm_is_opened!")
                    break
            cycle_idx += 1
            await asyncio.sleep(0.02)

    async def cycle_light_with_margin(self, threshold: int) -> None:
        cycle_idx = 0
        while True:
            resp = spi.xfer2([0x68, 0x00])  # SPI通信で値を読み込む
            volume = ((resp[0] << 8) + resp[1]) & 0x3FF  # 読み込んだ値を10ビットの数値に変換
            if cycle_idx == 0:
                stand_volume = [volume for _ in range(5)]
                detect_volume = [volume for _ in range(40)]
            else:
                stand_volume[cycle_idx % 5] = volume
                detect_volume[cycle_idx % 40] = volume
                idx_now = cycle_idx % 40
                if cycle_idx % 40 == 0:
                    print(sum(detect_volume) / 5, sum(stand_volume[-20:]) / 20)
                    assert len(stand_volume[-20:]) != 20
                    old_twenty_ave = sum(stand_volume[-20:]) / 20
                elif cycle_idx % 40 >= 20:
                    print(
                        sum(detect_volume) / 5,
                        sum(stand_volume[idx_now - 20 : idx_now - 1]) / 20,
                    )
                    assert stand_volume[idx_now - 20 : idx_now - 1] != 20
                    old_twenty_ave = sum(stand_volume[idx_now - 20 : idx_now - 1]) / 20
                else:
                    old_twenty_sum = sum(stand_volume[idx_now + 1 :]) + sum(
                        stand_volume[0 : 20 - len(sum(stand_volume[idx_now + 1 :]))]
                    )
                    print(sum(detect_volume) / 5, old_twenty_sum / 20)
                    assert stand_volume[idx_now + 1 :] + stand_volume[0 : 20 - len(sum(stand_volume[idx_now + 1 :]))]
                    old_twenty_ave = old_twenty_sum / 20
                recent_five_ave = sum(detect_volume) / len(detect_volume)
                if (recent_five_ave - old_twenty_ave) > threshold:
                    self.is_armopen = True
                    print("arm_is_opened!")
                    break
            cycle_idx += 1
            await asyncio.sleep(0.02)
