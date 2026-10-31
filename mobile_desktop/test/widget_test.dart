import 'package:flutter_test/flutter_test.dart';
import 'package:eesag_app/main.dart';

void main() {
  testWidgets('L’application EESAG se lance', (WidgetTester tester) async {
    await tester.pumpWidget(const EesagApp());

    expect(find.byType(EesagApp), findsOneWidget);
  });
}
