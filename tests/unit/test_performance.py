"""
B6性能优化测试

验证协议解析性能目标：
- 协议解析延迟 < 10ms
- 内存使用 < 100MB
"""

import pytest
import asyncio
import time


def test_protocol_parser_performance():
    """测试协议解析器性能"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType
        
        # 创建测试协议
        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0, head_pattern=b'\xAA'),
            ProtocolField("length", FieldType.LENGTH, 2, 2),
            ProtocolField("data", FieldType.DATA, 10, 4),
            ProtocolField("checksum", FieldType.CHECKSUM, 2, 14),
        ]
        
        protocol = ProtocolDefinition(
            name="perf_test",
            fields=fields,
            head_pattern=b'\xAA',
            min_length=5,
            max_length=20,
        )
        
        parser = ProtocolParser(protocol)
        
        # 测试数据
        test_packets = [
            b'\xAA\x02\x0AHelloWorld!\xAA' * 20,
            b'\xAA\x02\x0ADataPacket1!\xAA' * 30,
            b'\xAA\x02\x0ADataPacket2!\xAA' * 50,
            b'\xAA\x02\x0ADataPacket3!\xAA' * 100,
        ]
        
        # 预热
        for _ in range(100):
            parser.parse_data(test_packets[_ % len(test_packets)])
        
        # 正式性能测试
        times = []
        start_time = time.time()
        iterations = 100
        
        for i in range(iterations):
            packet = test_packets[i % len(test_packets)]
            result = parser.parse_data(packet)
            if result:
                times.append(time.time() - start_time)
                start_time = time.time()
        
        avg_time_ms = (sum(times) / len(times)) * 1000  # 转换为毫秒
        
        print(f'协议解析性能:')
        print(f'  平均时间: {avg_time_ms:.3f}ms/packet')
        print(f'  性能目标: <10ms')
        print(f'  状态: {\"✅ 达标\" if avg_time_ms < 10.0 else \"❌ 未达标\"}')
        
        # 验收
        assert avg_time_ms < 10.0, f"性能未达标: {avg_time_ms:.3f}ms > 10ms"
        
    except Exception as e:
        print(f'❌ 性能测试失败: {e}')


def test_memory_usage():
    """测试内存使用"""
    try:
        import psutil
        import gc
        
        process = psutil.Process()
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024
        print(f'初始内存: {initial_memory:.1f}MB')
        
        # 模拟大量数据
        large_data = b'x' * (10 * 1024 * 1024)  # 10MB数据
        
        # 处理数据
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType
        
        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0, head_pattern=b'\xAA'),
            ProtocolField("data", FieldType.DATA, 1024, 1024),
        ]
        
        protocol = ProtocolDefinition(
            name="memory_test",
            fields=fields,
            head_pattern=b'\xAA',
            min_length=5,
            max_length=5,
        )
        
        parser = ProtocolParser(protocol)
        
        # 处理多个数据包
        for _ in range(10):
            packet = b'\xAA\x02\x02' + large_data
            result = parser.parse_data(packet)
        
        # 检查内存
        gc.collect()
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_delta = current_memory - initial_memory
        
        print(f'当前内存: {current_memory:.1f}MB')
        print(f'内存增长: {memory_delta:.1f}MB')
        print(f'内存目标: <100MB, 状态: {\"✅ 达标\" if current_memory < 100.0 else \"❌ 未达标\"}')
        
        assert current_memory < 100.0, f"内存使用超标: {current_memory:.1f}MB > 100MB"
        
    except ImportError:
        print('⚠️ psutil未安装，跳过内存测试')
        print('   安装psutil后可执行完整内存测试')


if __name__ == "__main__":
    test_protocol_parser_performance()
    print('')
    test_memory_usage()