class CreatePrivacyTypes < ActiveRecord::Migration
  def change
    create_table :privacy_types do |t|
      t.string :name
      t.text :description

      t.timestamps null: false
    end
    add_index :privacy_types, :name
  end
end
