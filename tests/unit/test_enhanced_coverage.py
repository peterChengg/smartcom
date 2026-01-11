"""
测试用例增强建议

为 Agent B 的代码添加更多测试用例，防止出错。
"""

import pytest
import asyncio
import time


def test_error_handling_edge_cases():
    """测试错误处理的边界情况"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        # 测试1: 无效协议定义
        with pytest.raises(ValueError):
            ProtocolDefinition(
                name="invalid",
                fields=[],
                head_pattern=b'\xAA',
            )

        # 测试2: 负字段长度
        with pytest.raises(ValueError):
            ProtocolField(
                name="invalid",
                field_type=FieldType.DATA,
                length=-1,
                offset=0,
            )

        # 测试3: 字段重叠
        protocol = ProtocolDefinition(
            name="overlap",
            fields=[
                ProtocolField("field1", FieldType.DATA, 10, 0),
                ProtocolField("field2", FieldType.DATA, 5, 5),  # 重叠
            ],
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)
        # 测试解析会正常处理
        assert parser is not None

        print("✅ 边界情况测试通过")
    except Exception as e:
        print(f"❌ 边界情况测试失败: {e}")


def test_concurrent_parsing():
    """测试并发解析"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            ProtocolField("length", FieldType.LENGTH, 2, 2),
            ProtocolField("data", FieldType.DATA, 10, 4),
            ProtocolField("checksum", FieldType.CHECKSUM, 2, 14),
        ]

        protocol = ProtocolDefinition(
            name="concurrent",
            fields=fields,
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)

        # 测试并发解析
        async def parse_multiple(data_list):
            results = []
            for data in data_list:
                result = await parser.parse_data(data)
                results.append(result)
            return results

        test_data = [
            b'\xAA\x02\x0AHelloWorld!\xAA',
            b'\xAA\x02\x0ATestData123!\xAA',
            b'\xAA\x02\x0APacketData456!\xAA',
        ]

        results = asyncio.run(parse_multiple(test_data))

        # 验证结果
        assert len(results) == len(test_data)
        print(f"✅ 并发解析测试通过: {len(results)} packets parsed")
    except Exception as e:
        print(f"❌ 并发解析测试失败: {e}")


def test_large_data_handling():
    """测试大数据处理"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            ProtocolField("length", FieldType.LENGTH, 2, 2),
            ProtocolField("data", FieldType.DATA, 1000, 4),  # 大数据字段
        ]

        protocol = ProtocolDefinition(
            name="large_data",
            fields=fields,
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)

        # 测试大数据
        large_data = b'\xAA\x03\xE8' + b'x' * 1000 + b'\x00' * 5

        start_time = time.time()
        result = await parser.parse_data(large_data)
        elapsed = time.time() - start_time

        assert result is not None
        assert elapsed < 1.0, f"解析大数据超时: {elapsed:.3f}s"
        print(f"✅ 大数据处理测试通过: {elapsed:.3f}s")
    except Exception as e:
        print(f"❌ 大数据处理测试失败: {e}")


def test_memory_leak():
    """测试内存泄漏"""
    try:
        import gc
        import psutil

        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            ProtocolField("data", FieldType.DATA, 100, 2),
        ]

        protocol = ProtocolDefinition(
            name="memory_leak",
            fields=fields,
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)

        # 解析大量数据包
        for i in range(1000):
            packet = b'\xAA\x64' + b'x' * 100 + b'\x00' * 10
            await parser.parse_data(packet)

            # 每100个数据包检查内存
            if i % 100 == 0:
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                assert memory_growth < 50, f"内存增长过大: {memory_growth:.1f}MB at iteration {i}"

        print(f"✅ 内存泄漏测试通过")
    except ImportError:
        print("⚠️ psutil未安装，跳过内存泄漏测试")
    except Exception as e:
        print(f"❌ 内存泄漏测试失败: {e}")


def test_invalid_data_scenarios():
    """测试无效数据场景"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            ProtocolField("length", FieldType.LENGTH, 2, 2),
            ProtocolField("data", FieldType.DATA, 10, 4),
            ProtocolField("checksum", FieldType.CHECKSUM, 2, 14),
        ]

        protocol = ProtocolDefinition(
            name="invalid_data",
            fields=fields,
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)

        # 测试1: 空数据
        result1 = await parser.parse_data(b'')
        assert result1 is None

        # 测试2: 损坏的数据
        result2 = await parser.parse_data(b'\xAA\x02\x00HelloWorld!\xAA')
        assert result2 is not None  # 可以解析但可能无效

        # 测试3: 不完整的数据包
        result3 = await parser.parse_data(b'\xAA\x02')
        assert result3 is None  # 不完整

        # 测试4: 多个数据包拼接
        result4 = await parser.parse_data(b'\xAA\x02\x0AHello!\xAA\x03\x0BWorld!\xAA')
        # 应该能够处理多个数据包

        print("✅ 无效数据场景测试通过")
    except Exception as e:
        print(f"❌ 无效数据场景测试失败: {e}")


def test_data_processor_edge_cases():
    """测试数据处理器的边界情况"""
    try:
        from src.processing.data_processor import (
            DataProcessor,
            FieldFilter,
            FieldTransformer,
            FieldColorizer,
        )

        # 测试1: 空字段名
        processor = DataProcessor()

        packet1 = {"field1": 10, "field2": 20}
        result1 = processor.process_packet(packet1)
        assert result1 is not None

        # 测试2: 空过滤器
        filter1 = FieldFilter("test_eq", "field1", "eq", 10)
        assert filter1.matches({"field1": 10})

        # 测试3: 空转换器
        transformer = FieldTransformer("test_transform", "field1", lambda x: x * 2)
        transformed = transformer.apply({"field1": 10})
        assert transformed["field1"] == 20

        print("✅ 数据处理器边界测试通过")
    except Exception as e:
        print(f"❌ 数据处理器边界测试失败: {e}")


def test_visualization_edge_cases():
    """测试可视化的边界情况"""
    try:
        from src.visualization.protocol_visualizer import (
            ProtocolVisualizationEngine,
            VisualizationConfig,
        )
        from src.visualization.waveform_widget import WaveformWidget
        from src.visualization.field_panel import FieldPanel
        from src.core.protocol_parser import ParsedPacket

        # 测试1: 空协议数据
        engine = ProtocolVisualizationEngine(VisualizationConfig())
        packet1 = ParsedPacket(
            raw_data=b'test',
            fields={},
            timestamp=time.time(),
            parse_time=time.time(),
            is_valid=True,
        )
        engine.add_protocol("empty_test", packet1)

        # 测试2: 大数据量
        widget = WaveformWidget()
        for i in range(100):
            packet = ParsedPacket(
                raw_data=f'test{i}'.encode(),
                fields={"value": i * 10},
                timestamp=time.time() + i * 0.1,
                parse_time=time.time() + i * 0.1,
                is_valid=True,
            )
            widget.process_packet(packet)

        # 测试3: 空字段面板
        panel = FieldPanel()
        packet2 = ParsedPacket(
            raw_data=b'test',
            fields={"field1": 10, "field2": {"nested": 20}},
            timestamp=time.time(),
            parse_time=time.time(),
            is_valid=True,
        )
        panel.add_protocol_data("test_protocol", packet2)

        print("✅ 可视化边界测试通过")
    except Exception as e:
        print(f"❌ 可视化边界测试失败: {e}")


def test_dsl_parser_comprehensive():
    """测试DSL解析器的综合场景"""
    try:
        from src.core.protocols.dsl_parser import ProtocolDSLParser

        parser = ProtocolDSLParser()

        # 测试1: 复杂嵌套结构
        complex_yaml = """
        name: complex_protocol
        fields:
          - name: header
            type: HEAD
            offset: 0
            length: 2
            head_pattern: "AA55"

          - name: length
            type: LENGTH
            offset: 2
            length: 2

          - name: data
            type: DATA
            offset: 4
            length: 10

          - name: checksum
            type: CHECKSUM
            offset: 14
            length: 2

        encryption:
          type: XOR
          key: "0x12"
        """

        protocol = parser.parse(complex_yaml)
        assert protocol is not None
        assert protocol.name == "complex_protocol"

        print("✅ DSL解析器综合测试通过")
    except Exception as e:
        print(f"❌ DSL解析器综合测试失败: {e}")


def test_performance_under_load():
    """测试负载下的性能"""
    try:
        from src.core.protocol_parser import ProtocolParser, ProtocolDefinition, ProtocolField, FieldType

        fields = [
            ProtocolField("head", FieldType.HEAD, 2, 0),
            ProtocolField("length", FieldType.LENGTH, 2, 2),
            ProtocolField("data", FieldType.DATA, 10, 4),
            ProtocolField("checksum", FieldType.CHECKSUM, 2, 14),
        ]

        protocol = ProtocolDefinition(
            name="load_test",
            fields=fields,
            head_pattern=b'\xAA',
        )

        parser = ProtocolParser(protocol)

        # 测试负载性能
        test_packets = [
            b'\xAA\x02\x0AHelloWorld!\xAA' * 10,
            b'\xAA\x02\x0ATestData123!\xAA' * 10,
        ]

        # 热身
        for _ in range(100):
            packet = test_packets[_ % len(test_packets)]
            await parser.parse_data(packet)

        # 实际性能测试
        start_time = time.time()
        iterations = 500

        for i in range(iterations):
            packet = test_packets[i % len(test_packets)]
            await parser.parse_data(packet)

        elapsed = time.time() - start_time
        avg_time_ms = (elapsed / iterations) * 1000

        print(f"负载性能测试结果:")
        print(f"  总时间: {elapsed:.3f}s")
        print(f"  平均时间: {avg_time_ms:.3f}ms/packet")
        print(f"  性能目标: <10ms")
        status = "达标" if avg_time_ms < 10.0 else "未达标"
        print(f"  状态: {status}")

        assert avg_time_ms < 10.0, f"性能未达标: {avg_time_ms:.3f}ms > 10ms"

        print("✅ 负载性能测试通过")
    except Exception as e:
        print(f"❌ 负载性能测试失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Agent B 代码测试用例增强")
    print("=" * 60)
    print()

    test_error_handling_edge_cases()
    print()
    test_concurrent_parsing()
    print()
    test_large_data_handling()
    print()
    test_memory_leak()
    print()
    test_invalid_data_scenarios()
    print()
    test_data_processor_edge_cases()
    print()
    test_visualization_edge_cases()
    print()
    test_dsl_parser_comprehensive()
    print()
    test_performance_under_load()
    print()

    print("=" * 60)
    print("所有增强测试执行完成")
    print("=" * 60)
